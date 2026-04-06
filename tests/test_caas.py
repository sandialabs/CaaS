# © 2026 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government
# retains certain rights in this software.
#
# SPDX-License-Identifier: BSD-3-Clause

import json
from pathlib import Path

import pytest
from caas import (
    api,
    get_heartbeat,
    get_jobs,
    get_secrets,
    get_status,
    get_stream,
    get_version,
    read_output,
    remove_job,
    remove_secret,
    run_command,
    submit_job,
)
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles


@pytest.mark.xfail
def test_routes():
    assert api.routes == [
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


def test_url_path_for():
    assert api.url_path_for("get_heartbeat") == "/"
    assert api.url_path_for("submit_job") == "/job"
    assert api.url_path_for("remove_job") == "/job/delete"
    assert api.url_path_for("run_command") == "/job/exec"
    assert api.url_path_for("read_output") == "/job/output"
    assert api.url_path_for("get_status", uuid="asdf") == "/job/asdf/status"
    assert api.url_path_for("get_stream", uuid="asdf") == "/job/asdf/stream"
    assert api.url_path_for("get_jobs") == "/jobs"
    assert api.url_path_for("remove_secret") == "/secret/delete"
    assert api.url_path_for("get_secrets") == "/secrets"
    assert api.url_path_for("get_version") == "/version"


@pytest.fixture
def client(test_client_factory):
    with test_client_factory(api) as client_factory:
        yield client_factory


def test_get_heartbeat(client):  # pylint: disable=redefined-outer-name
    response = client.get("/")
    assert response.status_code == 200
    assert response.encoding == "utf-8"
    assert response.headers["content-type"] == "application/json"
    assert response.headers["content-length"] == "4"
    assert response.text == "null"


def test_get_version(client):  # pylint: disable=redefined-outer-name
    response = client.get("/version")
    assert response.status_code == 200
    assert response.encoding == "utf-8"
    assert response.headers["content-type"] == "application/json"


@pytest.mark.xfail
def test_get_jobs(mocker, client):
    mocker.patch("kubejob.list_jobs", return_value=["srbdev-12345"])
    response = client.get("/jobs")
    assert response.status_code == 200
    assert response.encoding == "utf-8"
    assert response.headers["content-type"] == "application/json"

    j = json.loads(response.text)
    assert type(j) == list
    assert j == ["srbdev-12345"]
