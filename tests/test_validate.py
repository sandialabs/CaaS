# © 2026 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government
# retains certain rights in this software.
#
# SPDX-License-Identifier: BSD-3-Clause

import uuid

import pytest
from validate import (
    set_none_if_empty,
    validate_cpu,
    validate_gpu,
    validate_memory,
    validate_secret,
)


@pytest.mark.parametrize(
    "input",
    [
        (None, None),
        ("", None),
        ("1", "1"),
        ("test", "test"),
        ("tEstIng", "tEstIng"),
    ],
)
def test_set_none_if_empty(input):
    assert set_none_if_empty(input[0]) == input[1]


# ~~~~~~~~~~~ Test for valid values ~~~~~~~~~~~ #
@pytest.mark.parametrize(
    "cpu", [("", 0.25), ("1", 1), (None, 0.25), (1, 1), ("300m", 0.3)]
)
def test_validate_cpu(cpu):
    assert validate_cpu(cpu[0]) == cpu[1]


@pytest.mark.parametrize("memory", [("", "61Mi"), ("1.86Gi", "1.86Gi"), (None, "61Mi")])
def test_validate_memory(memory):
    assert validate_memory(memory[0]) == memory[1]


@pytest.mark.parametrize("gpu", [("", 0), ("1", 1), (None, 0), (1, 1), (2, 2)])
def test_validate_gpu(gpu):
    assert validate_gpu(gpu[0]) == gpu[1]


# ~~~~~~~~~~~ Test for invalid values ~~~~~~~~~~~ #
@pytest.mark.parametrize("cpu", [5, -2, 300])
def test_invalid_cpu_value(cpu):
    with pytest.raises(ValueError) as e:
        validate_cpu(cpu)
    assert str(e.value) == "Invalid CPU value. Must request between 0 and 4 CPU."


@pytest.mark.parametrize("gpu", [3, -1, 100])
def test_invalid_gpu_value(gpu):
    with pytest.raises(ValueError) as e:
        validate_gpu(gpu)
    assert str(e.value) == "Invalid GPU value. Must request between 0 and 2 GPU."


@pytest.mark.parametrize("memory", ["33Gi", "-1Mi", "-12", "300", "300Gi"])
def test_invalid_memory_value(memory):
    with pytest.raises(ValueError) as e:
        validate_memory(memory)
    assert str(e.value) == "Invalid memory value. Must request between 0 and 32Gi."


@pytest.mark.parametrize(
    "secret",
    [
        ("srbdev", "abcd", f"srbdev-abcd-{uuid.uuid4().hex[:5]}", True),
        ("srbdev", "abcd", f"{uuid.uuid4().hex[:5]}", False),
        (None, None, f"srbdev-{uuid.uuid4().hex[:5]}", False),
        ({}, {}, f"srbdev-{uuid.uuid4().hex[:5]}", False),
        ([], [], f"srbdev-{uuid.uuid4().hex[:5]}", False),
        ("srbdev", "abcd", None, False),
        ("srbdev", "abcd", {}, False),
        ("srbdev", "abcd", [], False),
    ],
)
def test_validate_secret(secret):
    assert validate_secret(secret[0], secret[1], secret[2]) == secret[3]
