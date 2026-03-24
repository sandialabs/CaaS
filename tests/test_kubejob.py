import os
import sys
from unittest.mock import MagicMock

import pytest
from kubejob import (
    _get_pod,
    create_job,
    create_job_object,
    delete_job,
    list_jobs,
    read_job_status,
    read_pod_log,
    stream_stdout,
)
from kubernetes import client
from kubernetes.client.rest import ApiException


@pytest.fixture(autouse=True)
def setup():
    os.environ["CAAS_API_NAMESPACE"] = "testing"
    os.environ["CAAS_API_KUBERNETES_URL"] = "https://testing:1234"


def test_default_test_setup():
    assert os.getenv("CAAS_API_NAMESPACE") == "testing"
    assert os.getenv("CAAS_API_KUBERNETES_URL") == "https://testing:1234"


def test_create_job_object():
    username = "testuser"
    token = "abcd"
    uuid = "1234"
    container_image = "my-image:latest"
    registry_secret_name = None
    command = "echo Hello World"
    args = None
    aws_secret_name = None
    environment_variables = None
    writeable_mounts = None
    cpu = "100m"
    memory = "256Mi"
    gpu = None
    ttl_seconds_after_finished = 3600

    job = create_job_object(
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
    )

    assert job.metadata.name == f"{username}-{token}-{uuid}"
    assert job.spec.template.metadata.labels["job-type"] == "restricted"
    assert job.spec.template.spec.service_account_name == "no-access-sa"
    assert job.spec.ttl_seconds_after_finished == ttl_seconds_after_finished


def test_create_job_success():
    batch_mock = MagicMock()
    job_mock = MagicMock()
    result = create_job(batch_mock, job_mock)
    assert result is True
    batch_mock.create_namespaced_job.assert_called_once_with(
        body=job_mock, namespace=os.environ["CAAS_API_NAMESPACE"]
    )


def test_create_job_failure():
    batch_mock = MagicMock()
    job_mock = MagicMock()
    batch_mock.create_namespaced_job.side_effect = ApiException("API error")
    result = create_job(batch_mock, job_mock)
    assert result is False
    batch_mock.create_namespaced_job.assert_called_once_with(
        body=job_mock, namespace=os.environ["CAAS_API_NAMESPACE"]
    )


def test_list_jobs_success():
    batch_mock = MagicMock()
    job1 = MagicMock(metadata=MagicMock())
    job1.metadata.name = "testuser-abcd-job1"
    job2 = MagicMock(metadata=MagicMock())
    job2.metadata.name = "testuser-abcd-job2"
    job3 = MagicMock(metadata=MagicMock())
    job3.metadata.name = "otheruser-abcd-job3"
    batch_mock.list_namespaced_job.return_value = type(
        "obj", (object,), {"items": [job1, job2, job3]}
    )()
    result = list_jobs(batch_mock, "testuser", "abcd")
    assert result == ["job1", "job2"]
    batch_mock.list_namespaced_job.assert_called_once_with(
        namespace=os.environ["CAAS_API_NAMESPACE"]
    )


def test_list_jobs_failure():
    batch_mock = MagicMock()
    batch_mock.list_namespaced_job.side_effect = ApiException("API error")
    result = list_jobs(batch_mock, "testuser", "abcd")
    assert result is False
    batch_mock.list_namespaced_job.assert_called_once_with(
        namespace=os.environ["CAAS_API_NAMESPACE"]
    )


def test_get_pod_success():
    batch_mock = MagicMock()
    core_mock = MagicMock()
    username = "testuser"
    token = "abcd"
    uuid = "1234"
    job_mock = MagicMock(metadata=MagicMock(labels={"controller-uid": "some-uid"}))
    batch_mock.read_namespaced_job.return_value = job_mock
    pod_mock = MagicMock(metadata=MagicMock(name="pod1"))
    core_mock.list_namespaced_pod.return_value.items = [pod_mock]
    pod = _get_pod(batch_mock, core_mock, username, uuid)
    assert pod == pod_mock


def test_get_pod_job_not_found():
    batch_mock = MagicMock()
    core_mock = MagicMock()
    username = "testuser"
    token = "abcd"
    uuid = "1234"
    batch_mock.read_namespaced_job.side_effect = ApiException("Job not found")
    pod = _get_pod(batch_mock, core_mock, username, token, uuid)
    assert pod is None


def test_get_pod_success():
    batch_mock = MagicMock()
    core_mock = MagicMock()
    username = "testuser"
    token = "abcd"
    uuid = "1234"
    job_mock = MagicMock(metadata=MagicMock(labels={"controller-uid": "some-uid"}))
    batch_mock.read_namespaced_job.return_value = job_mock
    pod_mock = MagicMock(metadata=MagicMock(name="pod1"))
    core_mock.list_namespaced_pod.return_value.items = [pod_mock]
    pod = _get_pod(batch_mock, core_mock, username, token, uuid)
    assert pod == pod_mock


def test_get_pod_job_not_found():
    batch_mock = MagicMock()
    core_mock = MagicMock()
    username = "testuser"
    token = "abcd"
    uuid = "1234"
    batch_mock.read_namespaced_job.side_effect = ApiException("Job not found")
    pod = _get_pod(batch_mock, core_mock, username, token, uuid)
    assert pod is None


def test_get_pod_no_controller_uid():
    batch_mock = MagicMock()
    core_mock = MagicMock()
    username = "testuser"
    token = "abcd"
    uuid = "1234"
    job_mock = MagicMock(metadata=MagicMock(labels={}))
    batch_mock.read_namespaced_job.return_value = job_mock
    pod = _get_pod(batch_mock, core_mock, username, token, uuid)
    assert pod is None


def test_read_job_status_pending():
    batch_mock = MagicMock()
    core_mock = MagicMock()
    username = "testuser"
    token = "abcd"
    uuid = "1234"
    pod_mock = MagicMock(metadata=MagicMock(name="pod1"))
    batch_mock.read_namespaced_job.return_value = MagicMock(
        metadata=MagicMock(labels={"controller-uid": "some-uid"})
    )
    core_mock.list_namespaced_pod.return_value.items = [pod_mock]
    api_response = MagicMock(
        status=MagicMock(
            container_statuses=[
                MagicMock(
                    state=MagicMock(waiting=MagicMock(reason="ContainerCreating"))
                )
            ]
        )
    )
    core_mock.read_namespaced_pod_status.return_value = api_response
    status, message = read_job_status(batch_mock, core_mock, username, token, uuid)
    assert status == "pending"
    assert message is None


def test_read_pod_log_success():
    batch_mock = MagicMock()
    core_mock = MagicMock()
    username = "testuser"
    token = "abcd"
    uuid = "1234"
    since_seconds = 60
    tail_lines = 10
    pod_mock = MagicMock(metadata=MagicMock(name="pod1"))
    batch_mock.read_namespaced_job.return_value = MagicMock(
        metadata=MagicMock(labels={"controller-uid": "some-uid"})
    )
    core_mock.list_namespaced_pod.return_value.items = [pod_mock]
    expected_log = "This is the log output."
    core_mock.read_namespaced_pod_log.return_value = expected_log
    log = read_pod_log(
        batch_mock, core_mock, username, token, uuid, since_seconds, tail_lines
    )
    assert log == expected_log


def test_read_pod_log_success_take_with_nones():
    batch_mock = MagicMock()
    core_mock = MagicMock()
    username = "testuser"
    token = "abcd"
    uuid = "1234"
    pod_mock = MagicMock(metadata=MagicMock(name="pod1"))
    batch_mock.read_namespaced_job.return_value = MagicMock(
        metadata=MagicMock(labels={"controller-uid": "some-uid"})
    )
    core_mock.list_namespaced_pod.return_value.items = [pod_mock]
    expected_log = "This is the log output."
    core_mock.read_namespaced_pod_log.return_value = expected_log
    log = read_pod_log(batch_mock, core_mock, username, token, uuid, None, None)
    assert log == expected_log


def test_read_pod_log_api_exception():
    batch_mock = MagicMock()
    core_mock = MagicMock()
    username = "testuser"
    token = "abcd"
    uuid = "1234"
    since_seconds = 60
    tail_lines = 10
    pod_mock = MagicMock(metadata=MagicMock(name="pod1"))
    batch_mock.read_namespaced_job.return_value = MagicMock(
        metadata=MagicMock(labels={"controller-uid": "some-uid"})
    )
    core_mock.list_namespaced_pod.return_value.items = [pod_mock]
    core_mock.read_namespaced_pod_log.side_effect = ApiException("API error")
    log = read_pod_log(
        batch_mock, core_mock, username, token, uuid, since_seconds, tail_lines
    )
    assert log is None


def test_read_pod_log_invalid_since_seconds():
    batch_mock = MagicMock()
    core_mock = MagicMock()
    username = "testuser"
    token = "abcd"
    uuid = "1234"
    since_seconds = -1
    tail_lines = 10
    pod_mock = MagicMock(metadata=MagicMock(name="pod1"))
    batch_mock.read_namespaced_job.return_value = MagicMock(
        metadata=MagicMock(labels={"controller-uid": "some-uid"})
    )
    core_mock.list_namespaced_pod.return_value.items = [pod_mock]
    with pytest.raises(ValueError):
        read_pod_log(
            batch_mock, core_mock, username, token, uuid, since_seconds, tail_lines
        )


def test_read_pod_log_invalid_tail_lines():
    batch_mock = MagicMock()
    core_mock = MagicMock()
    username = "testuser"
    token = "abcd"
    uuid = "1234"
    since_seconds = 60
    tail_lines = -1
    pod_mock = MagicMock(metadata=MagicMock(name="pod1"))
    batch_mock.read_namespaced_job.return_value = MagicMock(
        metadata=MagicMock(labels={"controller-uid": "some-uid"})
    )
    core_mock.list_namespaced_pod.return_value.items = [pod_mock]
    with pytest.raises(ValueError):
        read_pod_log(
            batch_mock, core_mock, username, token, uuid, since_seconds, tail_lines
        )


def test_delete_job_success():
    batch_mock = MagicMock()
    username = "testuser"
    token = "abcd"
    uuid = "1234"
    result = delete_job(batch_mock, username, token, uuid)
    assert result is True
    batch_mock.delete_namespaced_job.assert_called_once_with(
        name=f"{username}-{token}-{uuid}",
        namespace=os.environ["CAAS_API_NAMESPACE"],
        body=client.V1DeleteOptions(
            propagation_policy="Foreground", grace_period_seconds=0
        ),
    )


def test_delete_job_failure():
    batch_mock = MagicMock()
    batch_mock.delete_namespaced_job.side_effect = ApiException("API error")
    username = "testuser"
    token = "abcd"
    uuid = "1234"
    result = delete_job(batch_mock, username, token, uuid)
    assert result is False
    batch_mock.delete_namespaced_job.assert_called_once_with(
        name=f"{username}-{token}-{uuid}",
        namespace=os.environ["CAAS_API_NAMESPACE"],
        body=client.V1DeleteOptions(
            propagation_policy="Foreground", grace_period_seconds=0
        ),
    )


def test_delete_job_not_found():
    batch_mock = MagicMock()
    batch_mock.delete_namespaced_job.side_effect = ApiException(
        status=404, reason="Not Found"
    )
    username = "testuser"
    token = "abcd"
    uuid = "1234"
    result = delete_job(batch_mock, username, token, uuid)
    assert result is False
    batch_mock.delete_namespaced_job.assert_called_once_with(
        name=f"{username}-{token}-{uuid}",
        namespace=os.environ["CAAS_API_NAMESPACE"],
        body=client.V1DeleteOptions(
            propagation_policy="Foreground", grace_period_seconds=0
        ),
    )


@pytest.mark.asyncio
async def test_stream_stdout_success():
    instance_mock = MagicMock()
    request_mock = MagicMock(user=MagicMock(username="testuser"))
    uuid = "1234"
    pod_event = {"raw_object": {"metadata": {"name": "testuser--abcd-1234-pod"}}}
    instance_mock.list_namespaced_pod = AsyncMock(return_value=[pod_event])
    log_event = "Log output"
    instance_mock.read_namespaced_pod_log = AsyncMock(return_value=[log_event])
    async for output in stream_stdout(instance_mock, request_mock, uuid):
        assert output == log_event


@pytest.mark.asyncio
async def test_stream_stdout_user_disconnection():
    instance_mock = MagicMock()
    request_mock = MagicMock(user=MagicMock(username="testuser"))
    uuid = "1234"
    pod_event = {"raw_object": {"metadata": {"name": "testuser-abcd-1234-pod"}}}
    instance_mock.list_namespaced_pod = AsyncMock(return_value=[pod_event])
    log_event = "Log output"
    instance_mock.read_namespaced_pod_log = AsyncMock(return_value=[log_event])
    request_mock.is_disconnected = AsyncMock(return_value=True)
    async for output in stream_stdout(instance_mock, request_mock, uuid):
        assert output == log_event
