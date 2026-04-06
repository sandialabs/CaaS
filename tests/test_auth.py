# © 2026 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government
# retains certain rights in this software.
#
# SPDX-License-Identifier: BSD-3-Clause

import pytest
from caas import api
from starlette.authentication import requires


@pytest.fixture
def client(test_client_factory):
    with test_client_factory(api) as client_factory:
        yield client_factory


def test_invalid_decorator_usage():
    with pytest.raises(Exception):

        @requires("api")
        def foo():  # pylint: disable=disallowed-name
            pass


def test_invalid_authentication_scheme(client):  # pylint: disable=redefined-outer-name
    response = client.post("/job", headers={"Authorization": "Foo testing"})
    assert response.status_code == 403
    assert response.encoding == "utf-8"
    assert response.headers["content-length"] == "9"
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert response.text == "Forbidden"


def test_unauthenticated_submit_job(client):  # pylint: disable=redefined-outer-name
    response = client.post("/job")
    assert response.status_code == 403
    assert response.encoding == "utf-8"
    assert response.headers["content-length"] == "9"
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert response.text == "Forbidden"


def test_unauthenticated_remove_job(client):  # pylint: disable=redefined-outer-name
    response = client.post("/job/delete")
    assert response.status_code == 403
    assert response.encoding == "utf-8"
    assert response.headers["content-length"] == "9"
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert response.text == "Forbidden"


def test_unauthenticated_run_command(client):  # pylint: disable=redefined-outer-name
    response = client.post("/job/exec")
    assert response.status_code == 403
    assert response.encoding == "utf-8"
    assert response.headers["content-length"] == "9"
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert response.text == "Forbidden"


def test_unauthenticated_read_output(client):  # pylint: disable=redefined-outer-name
    response = client.post("/job/output")
    assert response.status_code == 403
    assert response.encoding == "utf-8"
    assert response.headers["content-length"] == "9"
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert response.text == "Forbidden"


def test_unauthenticated_get_status(client):  # pylint: disable=redefined-outer-name
    response = client.get("/job/asdf/status")
    assert response.status_code == 403
    assert response.encoding == "utf-8"
    assert response.headers["content-length"] == "9"
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert response.text == "Forbidden"


def test_unauthenticated_get_stream(client):  # pylint: disable=redefined-outer-name
    response = client.get("/job/asdf/stream")
    assert response.status_code == 403
    assert response.encoding == "utf-8"
    assert response.headers["content-length"] == "9"
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert response.text == "Forbidden"


def test_unauthenticated_get_jobs(client):  # pylint: disable=redefined-outer-name
    response = client.get("/jobs")
    assert response.status_code == 403
    assert response.encoding == "utf-8"
    assert response.headers["content-length"] == "9"
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert response.text == "Forbidden"


def test_unauthenticated_remove_secrets(client):  # pylint: disable=redefined-outer-name
    response = client.post("/secret/delete")
    assert response.status_code == 403
    assert response.encoding == "utf-8"
    assert response.headers["content-length"] == "9"
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert response.text == "Forbidden"


def test_unauthenticated_get_secrets(client):  # pylint: disable=redefined-outer-name
    response = client.get("/secrets")
    assert response.status_code == 403
    assert response.encoding == "utf-8"
    assert response.headers["content-length"] == "9"
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert response.text == "Forbidden"
