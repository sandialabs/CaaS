# © 2026 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government
# retains certain rights in this software.
#
# SPDX-License-Identifier: BSD-3-Clause

from datetime import datetime

import pytest
from metrics import to_unix_timestamp

EXPECTED_UNIX_MILLISECONDS = 1752499168000


def test_datetime_object_input():
    dt = datetime(2025, 7, 14, 7, 19, 28)
    result = to_unix_timestamp(dt)
    assert result == EXPECTED_UNIX_MILLISECONDS


@pytest.mark.parametrize(
    "timestamp", ["2025-07-14 07:19:28", "2025-07-14T07:19:28", "2025-07-14T07:19:28Z"]
)
def test_string_formats(timestamp):
    result = to_unix_timestamp(timestamp)
    assert result == EXPECTED_UNIX_MILLISECONDS


@pytest.mark.parametrize(
    "timestamp", ["2025-07-14", "07/14/2025", "14/07/2025", "20250714"]
)
def test_date_only_formats(timestamp):
    expected_date = int(datetime(2025, 7, 14, 0, 0, 0).timestamp() * 1000)
    result = to_unix_timestamp(timestamp)
    assert result == expected_date


def test_numeric_input():
    unix = 1752499168000
    result = to_unix_timestamp(unix)
    assert result == EXPECTED_UNIX_MILLISECONDS


@pytest.mark.parametrize(
    "invalid",
    ["invalid-date", "2025-13-45 25:70:80", "not-a-timestamp", "", "2025/14/07"],
)
def test_invalid_string_format(invalid):
    with pytest.raises(ValueError, match="Unable to parse timestamp"):
        to_unix_timestamp(invalid)


@pytest.mark.parametrize("unsupported", [None, [], {}, set()])
def test_unsupported_type(unsupported):
    with pytest.raises(TypeError, match="Unsupported timestamp type"):
        to_unix_timestamp(unsupported)


def test_whitespace_handling():
    timestamp = "  2025-07-14 07:19:28  "
    result = to_unix_timestamp(timestamp)
    assert result == EXPECTED_UNIX_MILLISECONDS


@pytest.mark.parametrize(
    "timestamp",
    ["2025-07-14 07:19:28", datetime(2025, 7, 14, 7, 19, 28), 1752499168, 1752499168.0],
)
def test_parametrized_inputs(timestamp):
    result = to_unix_timestamp(timestamp)
    assert result == EXPECTED_UNIX_MILLISECONDS
