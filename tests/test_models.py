import uuid

import pytest
from models import JobDeletion, JobOutput, JobSubmission, UUIDPathParam
from pydantic import ValidationError


@pytest.mark.parametrize("model", [JobDeletion, JobOutput, UUIDPathParam])
def test_valid_uuid(model):
    valid_uuid = uuid.uuid4().hex
    param = model(uuid=valid_uuid)
    assert param.uuid == valid_uuid


@pytest.mark.parametrize("model", [JobDeletion, JobOutput, UUIDPathParam])
def test_empty_uuid(model):
    with pytest.raises(ValidationError):
        model(uuid="")


@pytest.mark.parametrize("model", [JobDeletion, JobOutput, UUIDPathParam])
def test_invalid_uuid(model):
    with pytest.raises(ValidationError):
        param = model(uuid="invalid-uuid")

    with pytest.raises(ValidationError):
        param = model(uuid="0123456789abcdef")

    with pytest.raises(ValidationError):
        param = model(uuid="0123456789abcdef0123456789abcdef0123456789abcdef")


@pytest.mark.parametrize("model", [JobDeletion, JobOutput, UUIDPathParam])
def test_frozen_uuid_path_param(model):
    valid_uuid = uuid.uuid4().hex
    param = model(uuid=valid_uuid)
    assert param.uuid == valid_uuid
    with pytest.raises(ValidationError):
        param.uuid = "new-uuid"
