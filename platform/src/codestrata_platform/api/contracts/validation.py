"""Response validation helpers for Platform DTOs."""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel, ValidationError

from codestrata_platform.application.common.errors import ValidationError as AppValidationError

T = TypeVar("T", bound=BaseModel)


def validate_response(model_type: type[T], payload: object) -> T:
    """Validate an outgoing payload against an explicit response DTO.

    Raises application ``ValidationError`` (mapped to HTTP 422) on failure so
    raw Pydantic exceptions do not cross the API boundary.
    """

    try:
        if isinstance(payload, model_type):
            return payload
        if isinstance(payload, BaseModel):
            return model_type.model_validate(payload.model_dump(mode="json"))
        return model_type.model_validate(payload)
    except ValidationError as error:
        preview = "; ".join(
            f"{'.'.join(str(part) for part in item.get('loc', ()))}: {item.get('msg')}"
            for item in error.errors()[:8]
        )
        raise AppValidationError(
            f"Response failed contract validation: {preview}",
            reason_code="response_validation_error",
        ) from error

