# © 2026 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government
# retains certain rights in this software.
#
# SPDX-License-Identifier: BSD-3-Clause

from typing import Optional

from pydantic import BaseModel, Field


class JobDeletion(BaseModel):
    uuid: str = Field(..., min_length=32, max_length=32, frozen=True)


class JobOutput(BaseModel):
    uuid: str = Field(..., min_length=32, max_length=32, frozen=True)
    since_seconds: Optional[str] = Field(default=None)
    tail_lines: Optional[str] = Field(default=None)


class UUIDPathParam(BaseModel):
    uuid: str = Field(..., min_length=32, max_length=32, frozen=True)


class JobSubmission(BaseModel):
    container_image: str = Field(..., min_length=1, frozen=True)
    registry_user: Optional[str] = Field(default=None)
    registry_password: Optional[str] = Field(default=None)
    command: Optional[str] = Field(default=None)
    args: Optional[str] = Field(default=None)
    aws_access_key_id: Optional[str] = Field(default=None)
    aws_secret_access_key: Optional[str] = Field(default=None)
    environment_variables: Optional[str] = Field(default=None)
    writeable_mounts: Optional[str] = Field(default=None)
    cpu: Optional[str] = Field(default="250m")
    memory: Optional[str] = Field(default="61Mi")
    gpu: Optional[str] = Field(default=None)
    ttl_seconds_after_finished: Optional[int] = Field(default=3600 * 24)


class SecretDeletion(BaseModel):
    # TODO: expand validation here, i.e. min_length, etc.
    name: str = Field(..., min_length=1, frozen=True)


class TokenCreation(BaseModel):
    pt: str = Field(..., min_length=1, frozen=True)
