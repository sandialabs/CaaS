# © 2026 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government
# retains certain rights in this software.
#
# SPDX-License-Identifier: BSD-3-Clause

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
