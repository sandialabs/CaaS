import base64
import binascii
import datetime
import hmac
import logging
import os
import secrets
import string
from hashlib import pbkdf2_hmac

from database import insert_new_user, select_user
from starlette.authentication import AuthenticationError

logger = logging.getLogger("caas.auth.token")


def generate_token_and_secret(username, pt):
    alphabet = string.ascii_letters + string.digits
    token_id = "".join(secrets.choice(alphabet) for _ in range(20)).upper()
    secret = "".join(secrets.choice(alphabet) for _ in range(40))

    # Salting secret before storing it in the database
    iterations = 500_000
    salt = os.getenv("CAAS_API_SALT")
    if salt is None:
        logger.critical("CAAS_API_SALT is not set!")
        return None, None
    salt = bytes.fromhex(salt)
    secret_bytes = bytes(secret, "utf-8")
    derived_key = pbkdf2_hmac("sha256", secret_bytes, salt * 2, iterations)
    timestamp = datetime.datetime.now()
    timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    insert_new_user(username, pt, token_id, derived_key.hex(), timestamp)

    logger.warning(f"new user created: {username} {extract_token_identifier(token_id)}")
    return token_id, secret


def extract_token_and_secret(authorization_header):
    try:
        scheme, credentials = authorization_header.split()
        if scheme.lower() != "basic":
            return
        decoded = base64.b64decode(credentials).decode("ascii")
        decoded = decoded.strip()
    except (ValueError, UnicodeDecodeError, binascii.Error) as e:
        raise AuthenticationError("Invalid basic auth credentials") from e

    token_id, _, secret = decoded.partition(":")
    return token_id, secret


def mask_token_id(token_id):
    safe_display_length = 4
    if len(token_id) >= safe_display_length:
        return (
            "*" * (len(token_id) - safe_display_length)
            + token_id[-safe_display_length:]
        )
    return token_id


def extract_token_identifier(token_id):
    return token_id[-4:].lower()


def authenticate_with_token(token, secret):
    """
    Fetches the hashed (and salted) secret from the database for the submitted
    token, and compares it with the submitted secret.

    See https://docs.python.org/3/library/hashlib.html#hashlib.pbkdf2_hmac for
    more information and details on suggested implementation(s).
    """
    user_row = select_user(token)
    if user_row is None:
        logger.debug(f"token={mask_token_id(token)} does not exist")
        return (False, None)

    user = dict(zip(["username", "token", "salted_secret_hash"], user_row))

    salt = os.getenv("CAAS_API_SALT")
    if salt is None:
        logger.critical("CAAS_API_SALT is not set!")
        return (False, None)

    salt_in_bytes = bytes.fromhex(salt)
    hash_for_token_in_bytes = bytes.fromhex(user["salted_secret_hash"])
    secret_in_bytes = bytes(secret, "utf-8")

    check = hmac.compare_digest(
        hash_for_token_in_bytes,
        pbkdf2_hmac("sha256", secret_in_bytes, salt_in_bytes * 2, 500_000),
    )

    return (check, user["username"])
