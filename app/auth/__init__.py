import logging

from starlette.authentication import AuthCredentials, AuthenticationBackend

from auth.token import (
    authenticate_with_token,
    extract_token_and_secret,
    extract_token_identifier,
)
from auth.users import SimpleApiUser

logger = logging.getLogger("caas.auth")


class BasicAuthenticationBackend(AuthenticationBackend):
    async def authenticate(self, conn):
        # Token-based API authentication and authorization
        if "Authorization" in conn.headers:
            auth = conn.headers["Authorization"]
            try:
                token_id, secret = extract_token_and_secret(auth)
            except:
                logger.error("error extracting token and secret")
                return

            (is_authenticated, username) = authenticate_with_token(token_id, secret)
            if is_authenticated is False:
                logger.warning(
                    f"{extract_token_identifier(token_id)} failed to authenticate"
                )
                return

            logger.info(
                f"{username} ({extract_token_identifier(token_id)}) successfully authenticated"
            )
            return AuthCredentials(["authenticated"]), SimpleApiUser(username, token_id)
        else:
            logger.debug("authentication header not supported")
            return
