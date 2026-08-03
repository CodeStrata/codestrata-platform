"""Deterministic JSON serialization helpers for Community Cloud API."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from starlette.responses import Response

from codestrata_platform.community_cloud_api.constants import (
    API_VERSION_HEADER,
    JSON_MEDIA_TYPE,
    REQUEST_ID_HEADER,
)
from codestrata_platform.community_cloud_api.errors import ApiErrorResponse, ErrorDetails


def to_stable_json_dict(value: object) -> Any:
    """Convert foundation objects / mappings into JSON-safe sorted structures."""

    if value is None or isinstance(value, (bool, int, float, str)):
        if isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
            raise ValueError("NaN/Infinity are not permitted in API JSON")
        return value
    if isinstance(value, Mapping):
        return {str(key): to_stable_json_dict(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [to_stable_json_dict(item) for item in value]
    if hasattr(value, "to_stable_dict") and callable(value.to_stable_dict):
        return to_stable_json_dict(value.to_stable_dict())
    raise TypeError(f"unsupported API serialization type: {type(value)!r}")


def dumps_stable(payload: object) -> bytes:
    """UTF-8 JSON with sorted keys, compact separators, trailing newline."""

    material = to_stable_json_dict(payload)
    return (
        json.dumps(
            material,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def build_json_response(
    payload: object,
    *,
    status_code: int,
    api_version: str,
    request_id: str | None = None,
    extra_headers: Mapping[str, str] | None = None,
) -> Response:
    """Build a deterministic JSON HTTP response."""

    headers = {
        "Content-Type": JSON_MEDIA_TYPE,
        API_VERSION_HEADER: api_version,
    }
    if request_id:
        headers[REQUEST_ID_HEADER] = request_id
    if extra_headers:
        for key in sorted(extra_headers, key=str):
            headers[str(key)] = str(extra_headers[key])
    return Response(
        content=dumps_stable(payload),
        status_code=status_code,
        media_type=JSON_MEDIA_TYPE,
        headers=headers,
    )


def build_error_response(
    code: str,
    *,
    http_status: int,
    api_version: str,
    request_id: str | None = None,
    details: ErrorDetails | None = None,
    message: str | None = None,
    meta_extra: Mapping[str, object] | None = None,
) -> Response:
    envelope = ApiErrorResponse.build(
        code,
        http_status=http_status,
        api_version=api_version,
        details=details,
        request_id=request_id,
        message=message,
        meta_extra=meta_extra,
    )
    return build_json_response(
        envelope,
        status_code=http_status,
        api_version=api_version,
        request_id=request_id,
    )
