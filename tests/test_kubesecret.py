# © 2026 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government
# retains certain rights in this software.
#
# SPDX-License-Identifier: BSD-3-Clause

import base64
import json
import os
from unittest.mock import MagicMock

import pytest
from kubernetes.client.rest import ApiException
from kubesecret import (
    create_opaque_secret,
    create_secret,
    delete_secret,
    generate_dockerconfigjson,
    list_secrets,
)


# Set up environment variables for testing
@pytest.fixture(autouse=True)
def setup():
    os.environ["CAAS_API_NAMESPACE"] = "testing"


def test_generate_dockerconfigjson():
    registry_url = "https://registry.example.com"
    registry_user = "testuser"
    registry_password = "testpassword"
    dockerconfigjson = generate_dockerconfigjson(
        registry_url, registry_user, registry_password
    )
    # Check that the generated dockerconfigjson is a valid base64 encoded string
    try:
        base64.b64decode(dockerconfigjson).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        assert False, "Invalid base64 encoded string"


def test_create_opaque_secret():
    core = MagicMock()
    name = "test-secret"
    data = {"key": "value"}
    encoded_data = {"key": "dmFsdWU="}
    secret = create_opaque_secret(core, name, data)
    # Check that the secret is created with the correct metadata and data
    assert secret.metadata.name == name
    assert secret.metadata.namespace == os.getenv("CAAS_API_NAMESPACE")
    assert secret.type == "Opaque"
    assert secret.data == encoded_data


def test_create_secret():
    core = MagicMock()
    name = "test-secret"
    registry_url = "https://registry.example.com"
    registry_user = "testuser"
    registry_password = "testpassword"
    secret = create_secret(core, name, registry_url, registry_user, registry_password)
    # Check that the secret is created with the correct metadata and data
    assert secret.metadata.name == name
    assert secret.metadata.namespace == os.getenv("CAAS_API_NAMESPACE")
    assert secret.type == "kubernetes.io/dockerconfigjson"
    dockerconfigjson = base64.b64decode(secret.data[".dockerconfigjson"]).decode(
        "utf-8"
    )
    assert json.loads(dockerconfigjson) == {
        "auths": {
            registry_url: {
                "auth": base64.b64encode(
                    f"{registry_user}:{registry_password}".encode("utf-8")
                ).decode("utf-8")
            }
        }
    }


def test_delete_secret():
    core = MagicMock()
    name = "test-secret"
    delete_secret(core, name)
    # Check that the delete_namespaced_secret method is called with the correct arguments
    core.delete_namespaced_secret.assert_called_once_with(
        name=name, namespace=os.getenv("CAAS_API_NAMESPACE")
    )


def test_list_secrets_empty():
    core = MagicMock()
    username = "testuser"
    token = "testtoken"
    core.list_namespaced_secret.return_value.items = []
    listed_secrets = list_secrets(core, username, token)
    # Check that an empty list is returned when there are no secrets
    assert listed_secrets == []


def test_list_secrets_api_error():
    core = MagicMock()
    username = "testuser"
    token = "testtoken"
    core.list_namespaced_secret.side_effect = ApiException("API error")
    listed_secrets = list_secrets(core, username, token)
    # Check that None is returned when an API error occurs
    assert listed_secrets is None
