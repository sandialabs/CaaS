# © 2026 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government
# retains certain rights in this software.
#
# SPDX-License-Identifier: BSD-3-Clause

import base64
import datetime
import os
from hashlib import pbkdf2_hmac
from unittest.mock import patch

from auth.token import (
    authenticate_with_token,
    extract_token_and_secret,
    extract_token_identifier,
    generate_token_and_secret,
    mask_token_id,
)


def test_extract_token_and_secret():
    token_id = "TESTTOKENID"
    secret = "testsecret"
    auth_header = f"Basic {base64.b64encode(f'{token_id}:{secret}'.encode()).decode()}"
    extracted_token_id, extracted_secret = extract_token_and_secret(auth_header)
    assert extracted_token_id == token_id
    assert extracted_secret == secret


def test_mask_token_id():
    token_id = "TESTTOKENID"
    masked_token_id = mask_token_id(token_id)
    assert masked_token_id == "*******" + token_id[-4:]


def test_extract_token_identifier():
    token_id = "TESTTOKENID"
    token_identifier = extract_token_identifier(token_id)
    assert token_identifier == token_id[-4:].lower()


def test_authenticate_with_token_valid_credentials():
    # Mock the select_user function to return a valid user
    user = {
        "username": "testuser",
        "token": "TESTTOKENID",
        "salted_secret_hash": pbkdf2_hmac(
            "sha256",
            "testsecret".encode(),
            bytes.fromhex(os.getenv("CAAS_API_SALT")) * 2,
            500_000,
        ).hex(),
    }

    with patch("auth.token.select_user") as mock_select_user:
        mock_select_user.return_value = (
            user["username"],
            user["token"],
            user["salted_secret_hash"],
        )

        token_id = user["token"]
        secret = "testsecret"
        authenticated, username = authenticate_with_token(token_id, secret)
        assert authenticated
        assert username == user["username"]
        mock_select_user.assert_called_once_with(token_id)


def test_authenticate_with_token_invalid_credentials():
    # Mock the select_user function to return a valid user
    user = {
        "username": "testuser",
        "token": "TESTTOKENID",
        "salted_secret_hash": pbkdf2_hmac(
            "sha256",
            "testsecret".encode(),
            bytes.fromhex(os.getenv("CAAS_API_SALT")) * 2,
            500_000,
        ).hex(),
    }

    with patch("auth.token.select_user") as mock_select_user:
        mock_select_user.return_value = (
            user["username"],
            user["token"],
            user["salted_secret_hash"],
        )

        token_id = user["token"]
        secret = "wrongsecret"
        authenticated, username = authenticate_with_token(token_id, secret)
        assert not authenticated
        assert username == "testuser"
        mock_select_user.assert_called_once_with(token_id)


def test_authenticate_with_token_invalid_token():
    with patch("auth.token.select_user") as mock_select_user:
        mock_select_user.return_value = None

        token_id = "INVALIDTOKENID"
        secret = "testsecret"
        authenticated, username = authenticate_with_token(token_id, secret)
        assert not authenticated
        assert username is None
        mock_select_user.assert_called_once_with(token_id)


def test_authenticate_with_token_missing_caas_api_salt():
    # Mock the os.getenv function to return None
    def mock_getenv(var):
        if var == "CAAS_API_SALT":
            return None
        return os.getenv(var)

    # Mock the select_user function to return a valid user
    user = {
        "username": "testuser",
        "token": "TESTTOKENID",
        "salted_secret_hash": pbkdf2_hmac(
            "sha256",
            "testsecret".encode(),
            bytes.fromhex(os.getenv("CAAS_API_SALT")) * 2,
            500_000,
        ).hex(),
    }

    with patch("os.getenv", mock_getenv), patch(
        "auth.token.select_user"
    ) as mock_select_user:
        mock_select_user.return_value = (
            user["username"],
            user["token"],
            user["salted_secret_hash"],
        )

        token_id = user["token"]
        secret = "testsecret"
        authenticated, username = authenticate_with_token(token_id, secret)
        assert not authenticated
        assert username is None
        mock_select_user.assert_called_once_with(token_id)
