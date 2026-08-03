"""Content-type / media-type helpers for Community Cloud API."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.constants import (
    ALLOWED_METHODS_WITH_JSON_BODY,
    JSON_MEDIA_TYPE,
)


def normalize_content_type(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip().lower()
    if not text:
        return None
    # Drop parameters (; charset=utf-8).
    return text.split(";", 1)[0].strip()


def requires_json_body(method: str) -> bool:
    return method.upper() in ALLOWED_METHODS_WITH_JSON_BODY


def is_json_content_type(value: str | None) -> bool:
    normalized = normalize_content_type(value)
    return normalized == JSON_MEDIA_TYPE
