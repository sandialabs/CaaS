# © 2026 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government
# retains certain rights in this software.
#
# SPDX-License-Identifier: BSD-3-Clause

import logging
import os
import sys

from kubernetes import client, config

logger = logging.getLogger("caas.kubeconfig")

HOST = os.getenv("CAAS_API_KUBERNETES_URL")


def get_kubernetes_api_instances():
    if "CAAS_API" in os.environ and os.environ["CAAS_API"] == "development":
        token = os.getenv("CAAS_KUBE_JOBS_TOKEN")
        if token is None:
            logger.critical("No CAAS_KUBE_JOBS_TOKEN environment specified. Exiting.")
            sys.exit(1)

        conf = client.Configuration()
        conf.host = HOST
        conf.api_key = {"authorization": f"Bearer {token}"}
        kube_c = client.ApiClient(conf)
        batch_v1 = client.BatchV1Api(kube_c)
        core_v1 = client.CoreV1Api(kube_c)
    elif "CAAS_API" in os.environ and os.environ["CAAS_API"] == "openshift":
        config.load_incluster_config()
        batch_v1 = client.BatchV1Api()
        core_v1 = client.CoreV1Api()
    elif "CAAS_API" in os.environ and os.environ["CAAS_API"] == "testing":
        batch_v1 = ""
        core_v1 = ""
    else:
        logger.critical("No CAAS_API environment specified. Exiting.")
        sys.exit(1)

    if (
        "CAAS_API_NAMESPACE" in os.environ
        and os.getenv("CAAS_API_NAMESPACE") == ""
        or os.getenv("CAAS_API_NAMESPACE") is None
    ):
        logger.critical("No CAAS_API_NAMESPACE specified. Exiting.")
        sys.exit(1)

    if (
        "CAAS_API_KUBERNETES_URL" in os.environ
        and os.getenv("CAAS_API_KUBERNETES_URL") == ""
        or os.getenv("CAAS_API_KUBERNETES_URL") is None
    ):
        logger.critical("No CAAS_API_KUBERNETES_URL specified. Exiting.")
        sys.exit(1)

    return (batch_v1, core_v1)
