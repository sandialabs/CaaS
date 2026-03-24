import logging
import os
import uuid
from logging.handlers import RotatingFileHandler

from auth import BasicAuthenticationBackend
from kubeconfig import get_kubernetes_api_instances
from kubejob import (
    create_job,
    create_job_object,
    delete_job,
    list_jobs,
    read_job_status,
    read_pod_log,
    stream_stdout,
)
from kubesecret import create_opaque_secret, create_secret, delete_secret, list_secrets
from models import JobDeletion, JobOutput, JobSubmission, SecretDeletion, UUIDPathParam
from pydantic import ValidationError
from sse_starlette.sse import EventSourceResponse
from starlette.applications import Starlette
from starlette.authentication import requires
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
from validate import (
    set_none_if_empty,
    validate_cpu,
    validate_gpu,
    validate_memory,
    validate_secret,
)

logger = logging.getLogger("caas")
logger.setLevel(logging.DEBUG)
# Setting up logging to stdout
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
# Setting up formatter to match (approximately) output from Uvicorn's logger
formatter = logging.Formatter("%(levelname)-9s %(asctime)s - %(name)s - %(message)s")
# Setting up logging to file on Openshift
if "CAAS_API" in os.environ and os.environ["CAAS_API"] == "openshift":
    file_handler = RotatingFileHandler(
        "/app/logs/caas-api.log", maxBytes=1024 * 1024 * 10
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

(batch_v1, core_v1) = get_kubernetes_api_instances()


async def log_request(request):
    if request.user.is_authenticated:
        logger.info(
            f"{request.user.username} ({request.user.token}) - {request.method} {request.url.path} from {request.client.host}:{request.client.port}"
        )
    else:
        logger.info(
            f"{request.method} {request.url.path} from {request.client.host}:{request.client.port}"
        )


# TODO: implement a log_response() function to log responses


async def get_heartbeat(request):
    await log_request(request)
    return JSONResponse(None)


@requires("authenticated")
async def submit_job(request):
    await log_request(request)
    async with request.form() as form:
        try:
            form_data = JobSubmission(**form)
            form_data.cpu = validate_cpu(form_data.cpu)
            form_data.memory = validate_memory(form_data.memory)
            form_data.gpu = validate_gpu(form_data.gpu)
        except ValidationError as e:
            logger.error(str(e))
            resp = {"uuid": None, "message": str(e)}
            return JSONResponse(resp, status_code=400)
        # 403 - permission denied to access resources
        except ValueError as e:
            logger.error(str(e))
            return JSONResponse(None, status_code=403)
        except Exception as e:
            logger.debug(str(e))
            return JSONResponse(None, status_code=400)

    # If username is suspected to be kerberos based on heuristic function in
    # validate.py, it will be caught above.
    # If registry_user didn't throw an error, we still need to
    # set_none_if_empty, validate not kerberos doesn't handle empty case
    form_data.registry_user = set_none_if_empty(form_data.registry_user)
    form_data.registry_password = set_none_if_empty(form_data.registry_password)
    # Additional form data validation
    form_data.command = set_none_if_empty(form_data.command)
    form_data.args = set_none_if_empty(form_data.args)
    form_data.aws_access_key_id = set_none_if_empty(form_data.aws_access_key_id)
    form_data.aws_secret_access_key = set_none_if_empty(form_data.aws_secret_access_key)
    form_data.environment_variables = set_none_if_empty(form_data.environment_variables)
    form_data.writeable_mounts = set_none_if_empty(form_data.writeable_mounts)

    job_uuid = uuid.uuid4().hex

    # Image pull secret management
    registry_secret_name = None
    if form_data.registry_user is not None and form_data.registry_password is not None:
        # The naming convention for Secrets stored in the vault in the
        # Openshift Kubernetes cluster is as follows:
        #
        #   f"{username}-{token}-{job_uuid[-5:]}-{uuid.uuid4().hex[-5:]}"
        #   i.e., srbdev-abcd-abc12-xyz34
        #
        registry_secret_name = f"{request.user.username}-{request.user.token}-{job_uuid[-5:]}-{uuid.uuid4().hex[-5:]}"

        # Inferring a registry's URL and port number from the
        # container_image field from the user in order to create a
        # dockerconfig JSON to store the private registry's credentials as
        # a Secret on Openshift.
        #
        # TODO:
        registry_url = ""

        registry_secret = create_secret(
            core_v1,
            registry_secret_name,
            registry_url,
            form_data.registry_user,
            form_data.registry_password,
        )
        if registry_secret is None:
            resp = {
                "uuid": None,
                "message": "Error creating Secret for private registry",
            }
            return JSONResponse(resp, status_code=500)
        # TODO: do I need to clean up secret for security reasons?

    aws_secret_name = None
    if (
        form_data.aws_access_key_id is not None
        and form_data.aws_secret_access_key is not None
    ):
        aws_secret_name = f"{request.user.username}-{request.user.token}-{job_uuid[-5:]}-{uuid.uuid4().hex[-5:]}"
        aws_secret_data = {
            "aws_access_key_id": form_data.aws_access_key_id,
            "aws_secret_access_key": form_data.aws_secret_access_key,
        }
        aws_secret = create_opaque_secret(core_v1, aws_secret_name, aws_secret_data)
        if aws_secret is None:
            resp = {
                "uuid": None,
                "message": "Error creating Secret for S3",
            }
            return JSONResponse(resp, status_code=500)
        # TODO: do I need to clean up secret for security reasons?

    job_object = create_job_object(
        request.user.username,
        request.user.token,
        job_uuid,
        form_data.container_image,
        registry_secret_name,
        form_data.command,
        form_data.args,
        aws_secret_name,
        form_data.environment_variables,
        form_data.writeable_mounts,
        form_data.cpu,
        form_data.memory,
        form_data.gpu,
        form_data.ttl_seconds_after_finished,
    )
    was_successful = create_job(batch_v1, job_object)

    if not was_successful:
        return JSONResponse(None, status_code=400)

    body = {"uuid": job_uuid, "message": None}
    return JSONResponse(body, status_code=200)


@requires("authenticated")
async def remove_job(request):
    await log_request(request)
    async with request.form() as form:
        try:
            form_data = JobDeletion(**form)
        except ValidationError as e:
            logger.debug(e.json())
            return JSONResponse(e.json(), status_code=400)
        except Exception as e:
            logger.debug(str(e))
            return JSONResponse(None, status_code=400)

    was_successful = delete_job(
        batch_v1, request.user.username, request.user.token, form_data.uuid
    )

    # Deletes associated Secrets
    secrets = list_secrets(
        core_v1,
        request.user.username,
        request.user.token,
    )
    for secret in secrets:
        if secret.startswith(
            f"{request.user.username}-{request.user.token}-{form_data.uuid[-5:]}-"
        ):
            delete_secret(core_v1, secret)

    if was_successful:
        status_code = 200
    else:
        status_code = 404

    return JSONResponse(None, status_code=status_code)


@requires("authenticated")
async def run_command(request):
    await log_request(request)
    headers = {
        "Access-Control-Expose-Headers": "Retry-After",
        "Retry-After": "Wed, 01 Oct 2025",
    }
    return JSONResponse(None, headers=headers, status_code=501)


@requires("authenticated")
async def read_output(request):
    await log_request(request)
    async with request.form() as form:
        try:
            form_data = JobOutput(**form)
        except ValidationError as e:
            logger.debug(e.json())
            return JSONResponse(e.json(), status_code=400)
        except Exception as e:
            logger.debug(str(e))
            return JSONResponse(None, status_code=400)

    form_data.since_seconds = set_none_if_empty(form_data.since_seconds)
    if form_data.since_seconds is not None:
        try:
            form_data.since_seconds = int(form_data.since_seconds, base=10)
        except ValueError:
            return JSONResponse(None, status_code=400)

    form_data.tail_lines = set_none_if_empty(form_data.tail_lines)
    if form_data.tail_lines is not None:
        try:
            form_data.tail_lines = int(form_data.tail_lines, base=10)
        except ValueError:
            return JSONResponse(None, status_code=400)

    # This method call an cause the API to run out of memory if the output is
    # too large.
    #
    # TODO: would the Kubernetes pod restart/heal itself if that's the case?
    # TODO: can it be prevented from the Kubernetes Python SDK?
    # TODO: can it be prevented from Python, i.e. by catching an out of memory
    # exception?
    #
    try:
        output = read_pod_log(
            batch_v1,
            core_v1,
            request.user.username,
            request.user.token,
            form_data.uuid,
            form_data.since_seconds,
            form_data.tail_lines,
        )
    except ValueError as e:
        logger.debug(str(e))
        return JSONResponse(None, status_code=500)

    if output is None:
        return JSONResponse(None, status_code=404)

    body = {"uuid": form_data.uuid, "output": output}
    return JSONResponse(body, status_code=200)


@requires("authenticated")
async def get_status(request):
    await log_request(request)
    try:
        job_uuid = UUIDPathParam(uuid=request.path_params["uuid"]).uuid
    except ValidationError as e:
        logger.debug(e.json())
        return JSONResponse(e.json(), status_code=400)
    status, message = read_job_status(
        batch_v1, core_v1, request.user.username, request.user.token, job_uuid
    )
    if status is None:
        return JSONResponse(None, status_code=404)

    body = {"uuid": job_uuid, "status": status, "message": message}
    return JSONResponse(body)


async def get_stream(request):
    await log_request(request)
    """
    Streams the data from a running job.

    Moved the authentication step away from the @requires("api") decorator, and
    into the method itself because of a bug where the route would automatically
    return a 403 with the decorator. And that was regardless of successful
    authentication.
    """
    is_authenticated = await BasicAuthenticationBackend().authenticate(request)
    if is_authenticated is None:
        return PlainTextResponse("Forbidden", status_code=403)

    try:
        job_uuid = UUIDPathParam(uuid=request.path_params["uuid"]).uuid
    except ValidationError as e:
        logger.debug(e.json())
        return PlainTextResponse("Bad Request", status_code=400)
    generator = stream_stdout(core_v1, request, job_uuid)
    return EventSourceResponse(generator)


@requires("authenticated")
async def get_jobs(request):
    await log_request(request)
    jobs = list_jobs(batch_v1, request.user.username, request.user.token)
    return JSONResponse(jobs, status_code=200)


@requires("authenticated")
async def remove_secret(request):
    await log_request(request)
    async with request.form() as form:
        try:
            form_data = SecretDeletion(**form)
        except ValidationError as e:
            logger.debug(str(e))
            return JSONResponse(e.json(), status_code=400)
        except Exception as e:
            logger.debug(str(e))
            return JSONResponse(None, status_code=400)

    # "Ensures" the user is allowed to use this secret.
    #
    # NOTE: It relies on the convention that secret names for Secrets
    # belonging to users follow the following convention:
    #
    #   f"{username}-{token}-{uuid.uuid4().hex[:5]}"
    #
    # FIXME: move validation inside the delete_secret method
    valid = validate_secret(request.user.username, request.user.token, form_data.name)
    if not valid:
        return JSONResponse(None, status_code=400)

    was_successful = delete_secret(core_v1, form_data.name)
    if was_successful:
        status_code = 200
    else:
        status_code = 404

    return JSONResponse(None, status_code=status_code)


@requires("authenticated")
async def get_secrets(request):
    await log_request(request)
    secrets = list_secrets(core_v1, request.user.username, request.user.token)
    return JSONResponse(secrets, status_code=200)


async def get_version(request):
    await log_request(request)
    return JSONResponse({"version": "0.8.1-alpha"})


routes = [
    Route("/", get_heartbeat),
    Route("/job", submit_job, methods=["POST"]),
    Route("/job/delete", remove_job, methods=["POST"]),
    Route("/job/exec", run_command, methods=["POST"]),
    Route("/job/output", read_output, methods=["POST"]),
    Route("/job/{uuid}/status", get_status),
    Route("/job/{uuid}/stream", get_stream),
    Route("/jobs", get_jobs),
    Route("/secret/delete", remove_secret, methods=["POST"]),
    Route("/secrets", get_secrets),
    Route("/version", get_version),
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST"],
        # TODO figure out which headers to whitelist
        allow_headers=["*"],
    ),
    Middleware(AuthenticationMiddleware, backend=BasicAuthenticationBackend()),
]

# TODO: set debug to False for v1
api = Starlette(debug=True, routes=routes, middleware=middleware)
