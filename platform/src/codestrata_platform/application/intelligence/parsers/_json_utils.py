"""Shared JSON parsing helpers for assessment intelligence parsers."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from codestrata_platform.application.common.errors import PayloadTooLargeError, ValidationError
from codestrata_platform.application.intelligence.parsers.limits import (
    MAX_JSON_DEPTH,
    MAX_METADATA_KEYS,
    MAX_STRING,
)

_SECRET_KEY_MARKERS = (
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "credential",
)


def load_json_object(content: bytes) -> dict[str, Any]:
    if not content:
        raise ValidationError("Artifact content is empty", reason_code="empty_artifact_content")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValidationError(
            "Artifact content must be UTF-8 encoded JSON",
            reason_code="invalid_artifact_encoding",
        ) from error
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValidationError(
            "Artifact content is not valid JSON",
            reason_code="invalid_json",
        ) from error
    if not isinstance(payload, dict):
        raise ValidationError(
            "Artifact JSON root must be an object",
            reason_code="invalid_json_root",
        )
    depth = _max_depth(payload)
    if depth > MAX_JSON_DEPTH:
        raise PayloadTooLargeError(
            f"Artifact JSON exceeds maximum depth of {MAX_JSON_DEPTH}",
            reason_code="json_depth_exceeded",
        )
    return payload


def require_string(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValidationError(
            f"Expected string for {field_name}",
            reason_code="invalid_field_type",
        )
    compact = value.strip()
    if not compact:
        raise ValidationError(
            f"{field_name} must be non-blank",
            reason_code="empty_field",
        )
    if len(compact) > MAX_STRING:
        raise ValidationError(
            f"{field_name} exceeds maximum length",
            reason_code="string_too_long",
        )
    return compact


def optional_string(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError(
            "Expected optional string field",
            reason_code="invalid_field_type",
        )
    compact = value.strip()
    if not compact:
        return None
    if len(compact) > MAX_STRING:
        raise ValidationError(
            "Optional string field exceeds maximum length",
            reason_code="string_too_long",
        )
    return compact


def optional_int(value: Any, *, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValidationError(
            f"{field_name} must be an integer",
            reason_code="invalid_field_type",
        )
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    raise ValidationError(
        f"{field_name} must be an integer",
        reason_code="invalid_field_type",
    )


def parse_metadata(raw: Any) -> dict[str, str]:
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        raise ValidationError(
            "Metadata must be an object",
            reason_code="invalid_metadata",
        )
    if len(raw) > MAX_METADATA_KEYS:
        raise PayloadTooLargeError(
            f"Metadata exceeds maximum key count of {MAX_METADATA_KEYS}",
            reason_code="metadata_too_large",
        )
    normalized: dict[str, str] = {}
    for key, value in raw.items():
        compact_key = require_string(key, field_name="metadata key")
        if not isinstance(value, str):
            raise ValidationError(
                "Metadata values must be strings",
                reason_code="invalid_metadata",
            )
        compact_value = require_string(value, field_name="metadata value")
        lowered = compact_key.lower()
        if any(marker in lowered for marker in _SECRET_KEY_MARKERS):
            raise ValidationError(
                f"Metadata key '{compact_key}' is not allowed",
                reason_code="secret_bearing_metadata",
            )
        normalized[compact_key] = compact_value
    return normalized


def _max_depth(value: Any, current: int = 1) -> int:
    if isinstance(value, dict):
        if not value:
            return current
        return max(_max_depth(item, current + 1) for item in value.values())
    if isinstance(value, list):
        if not value:
            return current
        return max(_max_depth(item, current + 1) for item in value)
    return current
