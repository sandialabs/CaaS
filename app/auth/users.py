from starlette.authentication import BaseUser

from auth.token import extract_token_identifier


class SimpleApiUser(BaseUser):
    def __init__(self, username: str, token: str) -> None:
        self.username = username
        self.token = extract_token_identifier(token)

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return self.username
