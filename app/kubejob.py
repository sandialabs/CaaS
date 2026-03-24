import ast
import logging
import os

from kubernetes import client, watch
from kubernetes.client import ApiTypeError
from kubernetes.client.rest import ApiException

logger = logging.getLogger("caas.kubejob")

NAMESPACE = os.getenv("CAAS_API_NAMESPACE")


def create_job(batch, job):
    try:
        batch.create_namespaced_job(body=job, namespace=NAMESPACE)
        return True
    except ApiException as e:
        logger.debug(str(e))
        return False


def create_job_object(
    username,
    token,
    uuid,
    container_image,
    registry_secret_name,
    command,
    args,
    aws_secret_name,
    environment_variables,
    writeable_mounts,
    cpu,
    memory,
    gpu,
    ttl_seconds_after_finished,
):  # pylint: disable=too-many-arguments, too-many-locals
    if command is not None:
        try:
            # Is this really safe to do? See documentation here
            # https://docs.python.org/3.11/library/ast.html#ast.literal_eval
            # for more information on the method.
            #
            # TODO: we may need to do additional parsing to make this try
            # section better and safer. The motivation behind adding the use of
            # `ast.literal_eval` is because a user may need to run something
            # like "['bash', '-c', 'echo test 2>/dev/null']", which won't work
            # with just the call to the `split` method because '2>/dev/null'
            # would be interpreted as a string and passed just as another
            # argument.
            c = ast.literal_eval(command)
            if type(c) == list:
                command = c
            else:
                command = command.split(" ")
        except Exception:
            command = command.split(" ")
    if args is not None:
        args = args.split(" ")

    resource_requests = {"cpu": cpu, "memory": memory}
    resource_limits = {"memory": memory}
    if gpu is not None:
        resource_requests["nvidia.com/gpu"] = gpu
        resource_limits["nvidia.com/gpu"] = gpu
    resources = client.V1ResourceRequirements(
        requests=resource_requests, limits=resource_limits
    )

    env = []
    if aws_secret_name is not None:
        env.append(
            client.V1EnvVar(
                name="AWS_ACCESS_KEY_ID",
                value_from=client.V1EnvVarSource(
                    secret_key_ref=client.V1SecretKeySelector(
                        "aws_access_key_id", aws_secret_name
                    )
                ),
            )
        )
        env.append(
            client.V1EnvVar(
                name="AWS_SECRET_ACCESS_KEY",
                value_from=client.V1EnvVarSource(
                    secret_key_ref=client.V1SecretKeySelector(
                        "aws_secret_access_key", aws_secret_name
                    )
                ),
            )
        )
    if environment_variables is not None:
        for environment_variable in environment_variables.split(","):
            variable = environment_variable.split("=")[0]
            value = environment_variable.split("=")[1]
            env.append(client.V1EnvVar(name=variable, value=value))

    volume_mounts = []
    volumes = []
    if writeable_mounts is not None:
        for path in writeable_mounts.split(","):
            name = path.replace("/", "")
            name = name.replace("_", "-")
            volume = client.V1Volume(name=name, empty_dir={})
            mount = client.V1VolumeMount(name=name, mount_path=path)
            volume_mounts.append(mount)
            volumes.append(volume)

    if registry_secret_name is not None:
        image_pull_policy = "Always"
    else:
        image_pull_policy = "IfNotPresent"

    container = client.V1Container(
        name=f"container-{uuid}",
        image=container_image,
        image_pull_policy=image_pull_policy,
        command=command,
        args=args,
        env=env,
        resources=resources,
        volume_mounts=volume_mounts,
    )

    image_pull_secrets = None
    if registry_secret_name is not None:
        image_pull_secrets = [client.V1LocalObjectReference(registry_secret_name)]

    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(
            labels={"app": NAMESPACE, "job-type": "restricted"}
        ),
        spec=client.V1PodSpec(
            restart_policy="Never",
            containers=[container],
            image_pull_secrets=image_pull_secrets,
            volumes=volumes,
            service_account_name="no-access-sa",
        ),
    )

    spec = client.V1JobSpec(
        template=template,
        backoff_limit=0,
        ttl_seconds_after_finished=ttl_seconds_after_finished,
    )

    job = client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(name=f"{username}-{token}-{uuid}"),
        spec=spec,
    )

    job_print_object = {
        "kind": job.kind,
        "name": job.metadata.name,
        "labels": job.spec.template.metadata.labels,
        "image": job.spec.template.spec.containers[0].image,
        "image_pull_secrets": job.spec.template.spec.image_pull_secrets,
        "image_pull_policy": job.spec.template.spec.containers[0].image_pull_policy,
        "resources": job.spec.template.spec.containers[0].resources.requests,
        "ttl_seconds_after_finished": job.spec.ttl_seconds_after_finished,
    }
    logger.debug(job_print_object)

    return job


def list_jobs(batch, username, token):
    try:
        jobs = []
        api_response = batch.list_namespaced_job(namespace=NAMESPACE)
        for job in api_response.items:
            if job.metadata.name.startswith(f"{username}-{token}-"):
                jobs.append(job.metadata.name.replace(f"{username}-{token}-", ""))

        return jobs
    except ApiException as e:
        logger.debug(str(e))
        return False


def delete_job(batch, username, token, uuid):
    try:
        batch.delete_namespaced_job(
            name=f"{username}-{token}-{uuid}",
            namespace=NAMESPACE,
            body=client.V1DeleteOptions(
                propagation_policy="Foreground", grace_period_seconds=0
            ),
        )
        logger.info(f"{username} ({token}) deleted job={uuid}")
        return True
    except ApiException as e:
        logger.debug(str(e))
        return False


def _get_pod(batch, core, username, token, uuid):
    try:
        job = batch.read_namespaced_job(
            name=f"{username}-{token}-{uuid}", namespace=NAMESPACE
        )
        controller_uid = job.metadata.labels.get("controller-uid")
        if controller_uid is None:
            return None

        pod_label = f"controller-uid={controller_uid}"
        pod_list = core.list_namespaced_pod(
            namespace=NAMESPACE, label_selector=pod_label
        ).items
        if len(pod_list) < 1:
            return None, None

        return pod_list[0]
    except ApiException as e:
        logger.debug(str(e))
        return None


def read_job_status(batch, core, username, token, uuid):
    logger.info(f"{username} ({token}) is checking status for job={uuid}")
    try:
        pod = _get_pod(batch, core, username, token, uuid)
        if pod is None:
            return None, None

        api_response = core.read_namespaced_pod_status(pod.metadata.name, NAMESPACE)
        container_state = api_response.status.container_statuses[0].state
        if (
            container_state.waiting is not None
            and container_state.waiting.reason == "ContainerCreating"
        ):
            return "pending", None
        elif container_state.waiting is not None:
            return container_state.waiting.reason, container_state.waiting.message
        elif container_state.running is not None:
            return "running", None
        elif container_state.terminated is not None:
            return (
                container_state.terminated.reason.lower(),
                container_state.terminated.message,
            )
        else:
            return "unknown", None
    except AttributeError as e:
        logger.debug(str(e))
        return None, None
    except ApiException as e:
        logger.debug(str(e))
        return None, None


def read_pod_log(batch, core, username, token, uuid, since_seconds, tail_lines):  # pylint: disable=too-many-arguments
    logger.info(f"{username} is reading output for job={uuid}")
    if since_seconds is not None and since_seconds < 0:
        raise ValueError("since_seconds must be a non-negative integer")
    if tail_lines is not None and tail_lines < 0:
        raise ValueError("tail_lines must be a non-negative integer")
    try:
        pod = _get_pod(batch, core, username, token, uuid)
        if pod is None:
            return None
        pod_name = pod.metadata.name
        log = core.read_namespaced_pod_log(
            name=pod_name,
            namespace=NAMESPACE,
            since_seconds=since_seconds,
            tail_lines=tail_lines,
        )
        return log
    except ApiException as e:
        logger.debug(str(e))
        return None


async def stream_stdout(instance, request, uuid):
    logger.info(
        f"{request.user.username} ({request.user.token}) is connected to stdout stream for job={uuid}"
    )
    w = watch.Watch()
    for event in w.stream(
        instance.list_namespaced_pod, namespace=NAMESPACE, timeout_seconds=2
    ):
        raw = event["raw_object"]
        metadata = raw["metadata"]
        name = metadata["name"]
        if name.startswith(f"{request.user.username}-{request.user.token}-{uuid}"):
            try:
                for event in w.stream(
                    instance.read_namespaced_pod_log, name=name, namespace=NAMESPACE
                ):
                    disconnected = await request.is_disconnected()
                    if disconnected:
                        logger.info(
                            f"{request.user.username} ({request.user.token}) has disconnected from the stream for job={uuid}"
                        )
                        break

                    yield event
                break
            except ApiTypeError:
                break
            except ApiException:
                break
