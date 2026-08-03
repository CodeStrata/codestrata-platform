"""Canonical request-body validation pipeline for Community Cloud API."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import ValidationError

from codestrata_platform.community_cloud_api.errors import (
    ERROR_BODY_FORBIDDEN,
    ERROR_BODY_REQUIRED,
    ERROR_INVALID_REQUEST_SCHEMA,
    ERROR_MALFORMED_JSON,
    ERROR_UNSUPPORTED_ASSESSMENT_HEAD,
    ERROR_UNSUPPORTED_ASSESSMENT_METADATA_SCHEMA,
    ERROR_UNSUPPORTED_CLI_EVENT_SCHEMA,
    ERROR_UNSUPPORTED_CLI_LIFECYCLE,
    ERROR_UNSUPPORTED_CLI_OPERATION,
    ERROR_UNSUPPORTED_CLI_RESULT,
    ERROR_UNSUPPORTED_EXTENSION_CLIENT,
    ERROR_UNSUPPORTED_EXTENSION_EDITOR,
    ERROR_UNSUPPORTED_EXTENSION_EVENT_SCHEMA,
    ERROR_UNSUPPORTED_EXTENSION_LIFECYCLE,
    ERROR_UNSUPPORTED_EXTENSION_OPERATION,
    ERROR_UNSUPPORTED_EXTENSION_RESULT,
    ERROR_UNSUPPORTED_AI_CAPABILITY,
    ERROR_UNSUPPORTED_AI_CLIENT,
    ERROR_UNSUPPORTED_AI_MODEL_FAMILY,
    ERROR_UNSUPPORTED_AI_OUTCOME,
    ERROR_UNSUPPORTED_AI_PROVIDER,
    ERROR_UNSUPPORTED_AI_USAGE_SCHEMA,
    ERROR_INVALID_AI_USAGE_COMBINATION,
    ERROR_UNSUPPORTED_JSON_SHAPE,
    ERROR_UNSUPPORTED_MEDIA_TYPE,
    ERROR_UNSUPPORTED_TELEMETRY_EVENT,
    ERROR_UNSUPPORTED_TELEMETRY_SCHEMA,
)
from codestrata_platform.community_cloud_api.media import is_json_content_type
from codestrata_platform.community_cloud_api.validation.errors import (
    FIELD_UNSAFE_VALUE,
    field_error,
    map_pydantic_error_type,
)
from codestrata_platform.community_cloud_api.validation.models import (
    BodyPolicy,
    CommunityApiRequestModel,
    RequestSchemaDescriptor,
    RequestValidationResult,
    SafeValidationDiagnostic,
    ValidationFieldError,
)
from codestrata_platform.community_cloud_api.validation.sanitization import (
    format_field_path,
)


def validate_request_body(
    *,
    descriptor: RequestSchemaDescriptor,
    body: bytes,
    content_type: str | None,
    route_name: str = "",
) -> RequestValidationResult:
    """Validate raw body bytes against a registered schema descriptor.

    Distinguishes malformed JSON, unsupported shapes, body policy failures,
    and schema-invalid payloads. Never returns submitted values in errors.
    """

    schema_id = descriptor.schema_id
    schema_version = descriptor.schema_version
    max_details = descriptor.max_error_details

    has_body = bool(body)
    policy = descriptor.body_policy

    if policy is BodyPolicy.FORBIDDEN:
        if has_body:
            return RequestValidationResult.fail(
                error_code=ERROR_BODY_FORBIDDEN,
                http_status=400,
                schema_id=schema_id,
                schema_version=schema_version,
            )
        return RequestValidationResult.ok(
            None, schema_id=schema_id, schema_version=schema_version
        )

    if not has_body:
        if policy is BodyPolicy.REQUIRED:
            return RequestValidationResult.fail(
                error_code=ERROR_BODY_REQUIRED,
                http_status=400,
                schema_id=schema_id,
                schema_version=schema_version,
            )
        # OPTIONAL + absent
        return RequestValidationResult.ok(
            None, schema_id=schema_id, schema_version=schema_version
        )

    # Body present — require JSON media type.
    if not is_json_content_type(content_type):
        return RequestValidationResult.fail(
            error_code=ERROR_UNSUPPORTED_MEDIA_TYPE,
            http_status=415,
            schema_id=schema_id,
            schema_version=schema_version,
        )

    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        return RequestValidationResult.fail(
            error_code=ERROR_MALFORMED_JSON,
            http_status=400,
            schema_id=schema_id,
            schema_version=schema_version,
        )

    try:
        parsed: Any = json.loads(text)
    except json.JSONDecodeError:
        return RequestValidationResult.fail(
            error_code=ERROR_MALFORMED_JSON,
            http_status=400,
            schema_id=schema_id,
            schema_version=schema_version,
        )

    if parsed is None:
        return RequestValidationResult.fail(
            error_code=ERROR_UNSUPPORTED_JSON_SHAPE,
            http_status=400,
            schema_id=schema_id,
            schema_version=schema_version,
            errors=(field_error("request", "invalid_type"),),
        )

    if not isinstance(parsed, dict):
        return RequestValidationResult.fail(
            error_code=ERROR_UNSUPPORTED_JSON_SHAPE,
            http_status=400,
            schema_id=schema_id,
            schema_version=schema_version,
            errors=(field_error("request", "invalid_type"),),
        )

    model_type = descriptor.model_type
    if model_type is None:
        return RequestValidationResult.fail(
            error_code=ERROR_INVALID_REQUEST_SCHEMA,
            http_status=422,
            schema_id=schema_id,
            schema_version=schema_version,
        )

    try:
        model = model_type.model_validate(parsed)
    except ValidationError as exc:
        errors, truncated = _map_pydantic_errors(exc, max_details=max_details)
        return RequestValidationResult.fail(
            error_code=_telemetry_aware_error_code(
                descriptor.schema_id, errors, ERROR_INVALID_REQUEST_SCHEMA
            ),
            http_status=422,
            schema_id=schema_id,
            schema_version=schema_version,
            errors=errors,
            truncated_error_count=truncated,
        )

    if descriptor.semantic_validator is not None:
        semantic_errors = list(descriptor.semantic_validator(model))
        if semantic_errors:
            ordered = _order_field_errors(semantic_errors)
            truncated = max(0, len(ordered) - max_details)
            return RequestValidationResult.fail(
                error_code=_telemetry_aware_error_code(
                    descriptor.schema_id, ordered, ERROR_INVALID_REQUEST_SCHEMA
                ),
                http_status=422,
                schema_id=schema_id,
                schema_version=schema_version,
                errors=ordered[:max_details],
                truncated_error_count=truncated,
            )

    return RequestValidationResult.ok(
        model, schema_id=schema_id, schema_version=schema_version
    )


def build_safe_diagnostic(
    *,
    route_name: str,
    result: RequestValidationResult,
) -> SafeValidationDiagnostic | None:
    if result.valid or not result.error_code:
        return None
    fields = tuple(sorted({item.field for item in result.errors}))
    return SafeValidationDiagnostic(
        route_name=route_name,
        error_code=result.error_code,
        field_names=fields,
        error_count=len(result.errors) + result.truncated_error_count,
        schema_id=result.schema_id,
    )


def _map_pydantic_errors(
    exc: ValidationError,
    *,
    max_details: int,
) -> tuple[tuple[ValidationFieldError, ...], int]:
    mapped: list[ValidationFieldError] = []
    seen: set[tuple[str, str]] = set()
    for item in exc.errors(include_url=False, include_context=False, include_input=False):
        field = format_field_path(item.get("loc") or ())
        raw_type = str(item.get("type") or "")
        # Detect custom unsafe marker from AfterValidators without echoing msg.
        msg = str(item.get("msg") or "")
        if "unsafe_value" in msg or "unsafe_value" in raw_type:
            code = FIELD_UNSAFE_VALUE
        elif "invalid_enum" in msg:
            code = "invalid_enum"
        elif "invalid_format" in msg:
            code = "invalid_format"
        elif "too_short" in msg:
            code = FIELD_TOO_SHORT
        elif "too_long" in msg:
            code = FIELD_TOO_LONG
        else:
            code = map_pydantic_error_type(raw_type)
        key = (field, code)
        if key in seen:
            continue
        seen.add(key)
        mapped.append(field_error(field, code))

    ordered = _order_field_errors(mapped)
    truncated = max(0, len(ordered) - max_details)
    return tuple(ordered[:max_details]), truncated


def _order_field_errors(
    errors: Sequence[ValidationFieldError],
) -> list[ValidationFieldError]:
    return sorted(errors, key=lambda item: (item.field, item.code, item.message))


def _telemetry_aware_error_code(
    schema_id: str,
    errors: Sequence[ValidationFieldError],
    default: str,
) -> str:
    """Map schema-specific validation failures to dedicated top-level codes."""

    fields = {item.field for item in errors}
    if schema_id == "community.telemetry.ingest":
        if "schema_version" in fields:
            return ERROR_UNSUPPORTED_TELEMETRY_SCHEMA
        if "event_type" in fields:
            return ERROR_UNSUPPORTED_TELEMETRY_EVENT
        return default
    if schema_id == "community.assessment-metadata.ingest":
        if "schema_version" in fields:
            return ERROR_UNSUPPORTED_ASSESSMENT_METADATA_SCHEMA
        if any(
            field.endswith("executed_heads") or field == "assessment.executed_heads"
            for field in fields
        ):
            if any(
                item.field.endswith("executed_heads") and item.code == "invalid_enum"
                for item in errors
            ):
                return ERROR_UNSUPPORTED_ASSESSMENT_HEAD
        return default
    if schema_id == "community.cli-events.ingest":
        if "schema_version" in fields:
            return ERROR_UNSUPPORTED_CLI_EVENT_SCHEMA
        if "event.operation" in fields:
            return ERROR_UNSUPPORTED_CLI_OPERATION
        if "event.lifecycle" in fields:
            return ERROR_UNSUPPORTED_CLI_LIFECYCLE
        if "event.result" in fields:
            return ERROR_UNSUPPORTED_CLI_RESULT
        return default
    if schema_id == "community.extension-events.ingest":
        if "schema_version" in fields:
            return ERROR_UNSUPPORTED_EXTENSION_EVENT_SCHEMA
        if "client.name" in fields:
            return ERROR_UNSUPPORTED_EXTENSION_CLIENT
        if "client.editor" in fields:
            return ERROR_UNSUPPORTED_EXTENSION_EDITOR
        if "event.operation" in fields:
            return ERROR_UNSUPPORTED_EXTENSION_OPERATION
        if "event.lifecycle" in fields:
            return ERROR_UNSUPPORTED_EXTENSION_LIFECYCLE
        if "event.result" in fields:
            return ERROR_UNSUPPORTED_EXTENSION_RESULT
        return default
    if schema_id == "community.ai-usage.ingest":
        if "schema_version" in fields:
            return ERROR_UNSUPPORTED_AI_USAGE_SCHEMA
        if "client.name" in fields:
            return ERROR_UNSUPPORTED_AI_CLIENT
        if "usage.capability" in fields:
            return ERROR_UNSUPPORTED_AI_CAPABILITY
        if "usage.provider_family" in fields:
            return ERROR_UNSUPPORTED_AI_PROVIDER
        if "usage.model_family" in fields:
            return ERROR_UNSUPPORTED_AI_MODEL_FAMILY
        if "usage.outcome" in fields:
            return ERROR_UNSUPPORTED_AI_OUTCOME
        if any(
            field.startswith("usage.")
            and item.code == "invalid_enum"
            for field in fields
            for item in errors
            if item.field == field
        ):
            # Token/outcome combination failures map to dedicated code when
            # usage.* fields fail semantic rules beyond simple enum catalogs.
            usage_fields = {
                "usage.input_token_bucket",
                "usage.output_token_bucket",
                "usage.total_token_bucket",
                "usage.failure_category",
            }
            if fields & usage_fields:
                return ERROR_INVALID_AI_USAGE_COMBINATION
        return default
    return default


def ensure_mapping(value: object) -> Mapping[str, Any] | None:
    if isinstance(value, Mapping):
        return value  # type: ignore[return-value]
    return None
