# © 2026 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government
# retains certain rights in this software.
#
# SPDX-License-Identifier: BSD-3-Clause

import base64
import json
import logging
import os

from kubernetes import client
from kubernetes.client.rest import ApiException

logger = logging.getLogger("caas.kubesecret")

NAMESPACE = os.getenv("CAAS_API_NAMESPACE")


def generate_dockerconfigjson(registry_url, registry_user, registry_password):
    user_password = f"{registry_user}:{registry_password}"
    auth = base64.b64encode(bytes(user_password, "utf-8")).decode("ascii")
    dockerconfigjson = {"auths": {f"{registry_url}": {"auth": auth}}}
    dockerconfigjson_bytes = bytes(json.dumps(dockerconfigjson), "utf-8")
    return base64.b64encode(dockerconfigjson_bytes).decode("ascii")


def encode_values(data):
    """Base64 encodes all values in a dictionary.

    Args:
        data (dict)

    Returns:
        dict: A new dictionary with base64 encoded values
    """
    encoded = {}
    for key, value in data.items():
        if isinstance(value, str):
            value_in_bytes = bytes(value, "utf-8")
            encode_value = base64.b64encode(value_in_bytes).decode("utf-8")
            encoded[key] = encode_value
        else:
            logger.error(f"caught a non-string value for key={key}")
    return encoded


def create_opaque_secret(core, name, data):
    """Creates an a Kubernetes Secret of type Opaque, from a dictionary.

    Args:
        core (kubernetes.client.CoreV1Api)
        name (str): Name of the new Secret
        data (dict[str, str])
    """
    logger.info(f"creating secret {name}")
    try:
        secret_labels = {
            "type": "dynamic",
            "tier": "user",
        }
        secret = client.V1Secret()
        secret.metadata = client.V1ObjectMeta(
            name=name, namespace=NAMESPACE, labels=secret_labels
        )
        secret.type = "Opaque"
        secret.data = encode_values(data)
        secret.immutable = True
        core.create_namespaced_secret(namespace=NAMESPACE, body=secret)
        return secret
        # TODO: do I need to clean up data for security reasons?
    except ApiException as e:
        logger.debug(str(e))
        return None
    except Exception as e:
        logger.debug(e)
        return None


def create_secret(core, name, registry_url, registry_user, registry_password):
    logger.info(f"creating secret {name}")
    try:
        dockerconfigjson = generate_dockerconfigjson(
            registry_url, registry_user, registry_password
        )

        secret_labels = {
            "type": "dynamic",
            "tier": "user",
        }
        secret = client.V1Secret()
        secret.metadata = client.V1ObjectMeta(
            name=name, namespace=NAMESPACE, labels=secret_labels
        )
        secret.type = "kubernetes.io/dockerconfigjson"
        secret.data = {".dockerconfigjson": dockerconfigjson}
        secret.immutable = True
        core.create_namespaced_secret(namespace=NAMESPACE, body=secret)
        return secret
    except ApiException as e:
        logger.debug(str(e))
        return None
    except Exception as e:
        logger.debug(e)
        return None


def delete_secret(core, name):
    logger.info(f"deleting secret {name}")
    try:
        core.delete_namespaced_secret(name=name, namespace=NAMESPACE)
        return True
    except ApiException as e:
        logger.debug(str(e))
        return False


def list_secrets(core, username, token):
    try:
        secrets = []
        api_response = core.list_namespaced_secret(namespace=NAMESPACE)
        for secret in api_response.items:
            if secret.metadata.name.startswith(f"{username}-{token}-"):
                secrets.append(secret.metadata.name)
        return secrets
    except ApiException as e:
        logger.debug(str(e))
        return None
