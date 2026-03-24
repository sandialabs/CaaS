import os

import pytest
from kubeconfig import get_kubernetes_api_instances


@pytest.fixture(autouse=True)
def setup():
    os.environ["CAAS_API_NAMESPACE"] = "testing"
    os.environ["CAAS_API_KUBERNETES_URL"] = "https://testing:1234"


def test_default_test_setup():
    assert os.getenv("CAAS_API_NAMESPACE") == "testing"
    assert os.getenv("CAAS_API_KUBERNETES_URL") == "https://testing:1234"
    get_kubernetes_api_instances()


def test_missing_namespace():
    assert os.getenv("CAAS_API_NAMESPACE") == "testing"
    assert os.getenv("CAAS_API_KUBERNETES_URL") == "https://testing:1234"

    del os.environ["CAAS_API_NAMESPACE"]
    with pytest.raises(SystemExit) as e:
        get_kubernetes_api_instances()
    assert e.type == SystemExit
    assert e.value.code == 1


def test_missing_kubernetes_url():
    assert os.getenv("CAAS_API_NAMESPACE") == "testing"
    assert os.getenv("CAAS_API_KUBERNETES_URL") == "https://testing:1234"

    del os.environ["CAAS_API_KUBERNETES_URL"]
    with pytest.raises(SystemExit) as e:
        get_kubernetes_api_instances()
    assert e.type == SystemExit
    assert e.value.code == 1
