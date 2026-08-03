"""Canonical validation error codes and safe field-error mapping."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from codestrata_platform.community_cloud_api.errors import (
    ERROR_BODY_FORBIDDEN,
    ERROR_BODY_REQUIRED,
    ERROR_INVALID_REQUEST_SCHEMA,
    ERROR_MALFORMED_JSON,
    ERROR_UNSUPPORTED_JSON_SHAPE,
    ERROR_UNSUPPORTED_MEDIA_TYPE,
    ApiErrorResponse,
)
from codestrata_platform.community_cloud_api.validation.models import (
    RequestValidationResult,
    ValidationFieldError,
)

# Field-level codes (never free-form exception class names).
FIELD_MISSING = "missing"
FIELD_UNKNOWN = "unknown_field"
FIELD_INVALID_TYPE = "invalid_type"
FIELD_TOO_SHORT = "too_short"
FIELD_TOO_LONG = "too_long"
FIELD_TOO_SMALL = "too_small"
FIELD_TOO_LARGE = "too_large"
FIELD_INVALID_FORMAT = "invalid_format"
FIELD_INVALID_ENUM = "invalid_enum"
FIELD_UNSAFE_VALUE = "unsafe_value"
FIELD_INVALID = "invalid"

_FIELD_MESSAGES: dict[str, str] = {
    FIELD_MISSING: "Required field is missing.",
    FIELD_UNKNOWN: "Unknown field is not permitted.",
    FIELD_INVALID_TYPE: "Field has an invalid type.",
    FIELD_TOO_SHORT: "Value is shorter than the minimum length.",
    FIELD_TOO_LONG: "Value exceeds the maximum length.",
    FIELD_TOO_SMALL: "Value is below the minimum.",
    FIELD_TOO_LARGE: "Value exceeds the maximum.",
    FIELD_INVALID_FORMAT: "Value does not match the required format.",
    FIELD_INVALID_ENUM: "Value is not an allowed option.",
    FIELD_UNSAFE_VALUE: "Value is not permitted.",
    FIELD_INVALID: "Field failed validation.",
}

# Map Pydantic v2 error types → safe field codes (no values / class names).
_PYDANTIC_TYPE_TO_CODE: dict[str, str] = {
    "missing": FIELD_MISSING,
    "extra_forbidden": FIELD_UNKNOWN,
    "string_type": FIELD_INVALID_TYPE,
    "int_type": FIELD_INVALID_TYPE,
    "float_type": FIELD_INVALID_TYPE,
    "bool_type": FIELD_INVALID_TYPE,
    "list_type": FIELD_INVALID_TYPE,
    "dict_type": FIELD_INVALID_TYPE,
    "none_required": FIELD_INVALID_TYPE,
    "string_too_short": FIELD_TOO_SHORT,
    "string_too_long": FIELD_TOO_LONG,
    "too_short": FIELD_TOO_SHORT,
    "too_long": FIELD_TOO_LONG,
    "greater_than_equal": FIELD_TOO_SMALL,
    "greater_than": FIELD_TOO_SMALL,
    "less_than_equal": FIELD_TOO_LARGE,
    "less_than": FIELD_TOO_LARGE,
    "string_pattern_mismatch": FIELD_INVALID_FORMAT,
    "enum": FIELD_INVALID_ENUM,
    "literal_error": FIELD_INVALID_ENUM,
    "value_error": FIELD_INVALID,
}


def field_error(field: str, code: str) -> ValidationFieldError:
    safe_code = code if code in _FIELD_MESSAGES else FIELD_INVALID
    return ValidationFieldError(
        field=field,
        code=safe_code,
        message=_FIELD_MESSAGES[safe_code],
    )


def map_pydantic_error_type(error_type: str) -> str:
    text = (error_type or "").strip()
    if text in _PYDANTIC_TYPE_TO_CODE:
        return _PYDANTIC_TYPE_TO_CODE[text]
    # Custom validators may raise value_error.* — treat unsafe marker specially.
    if "unsafe" in text.lower():
        return FIELD_UNSAFE_VALUE
    if text.startswith("value_error"):
        return FIELD_INVALID
    return FIELD_INVALID


def build_validation_error_response(
    result: RequestValidationResult,
    *,
    api_version: str,
    request_id: str | None = None,
) -> ApiErrorResponse:
    """Build canonical API error envelope from a failed validation result."""

    if result.valid or not result.error_code or not result.http_status:
        raise ValueError("build_validation_error_response requires a failed result")

    details: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None
    if result.errors:
        details = [item.to_stable_dict() for item in result.errors]
    else:
        details = None

    meta_extra: dict[str, Any] = {
        "schema_id": result.schema_id,
        "schema_version": result.schema_version,
        "validation_error_count": len(result.errors) + result.truncated_error_count,
        "validation_errors_returned": len(result.errors),
    }
    if result.truncated_error_count:
        meta_extra["additional_error_count"] = result.truncated_error_count

    return ApiErrorResponse.build(
        result.error_code,
        http_status=result.http_status,
        api_version=api_version,
        details=details,
        request_id=request_id,
        meta_extra=meta_extra,
    )


# Re-export top-level codes for validators/tests.
__all__ = [
    "ERROR_BODY_FORBIDDEN",
    "ERROR_BODY_REQUIRED",
    "ERROR_INVALID_REQUEST_SCHEMA",
    "ERROR_MALFORMED_JSON",
    "ERROR_UNSUPPORTED_JSON_SHAPE",
    "ERROR_UNSUPPORTED_MEDIA_TYPE",
    "FIELD_INVALID",
    "FIELD_INVALID_ENUM",
    "FIELD_INVALID_FORMAT",
    "FIELD_INVALID_TYPE",
    "FIELD_MISSING",
    "FIELD_TOO_LARGE",
    "FIELD_TOO_LONG",
    "FIELD_TOO_SHORT",
    "FIELD_TOO_SMALL",
    "FIELD_UNKNOWN",
    "FIELD_UNSAFE_VALUE",
    "build_validation_error_response",
    "field_error",
    "map_pydantic_error_type",
]
