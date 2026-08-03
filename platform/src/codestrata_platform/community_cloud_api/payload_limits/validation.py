"""Deterministic payload-size and structural-limit validation."""

from __future__ import annotations

import json
from typing import Any

from codestrata_platform.community_cloud_api.errors import (
    ERROR_PAYLOAD_ARRAY_LIMIT,
    ERROR_PAYLOAD_COMPLEXITY_LIMIT,
    ERROR_PAYLOAD_OBJECT_LIMIT,
    ERROR_PAYLOAD_STRING_LIMIT,
    ERROR_PAYLOAD_TOO_DEEP,
    ERROR_PAYLOAD_TOO_LARGE,
)
from codestrata_platform.community_cloud_api.payload_limits.models import (
    PayloadLimitPolicy,
    PayloadLimitResult,
)
from codestrata_platform.community_cloud_api.payload_limits.policy import (
    assert_supported_policy,
)

HTTP_PAYLOAD_TOO_LARGE = 413


def enforce_payload_limits(
    *,
    body: bytes,
    policy: PayloadLimitPolicy | None = None,
    parsed: Any | None = None,
) -> PayloadLimitResult:
    """Enforce byte-size and JSON structural limits.

    Call after route resolution and (when applicable) after Slice 7.3 request
    validation succeeds. Empty bodies are accepted without structural checks.
    Never echoes payload contents.
    """

    active = assert_supported_policy(policy or PayloadLimitPolicy.default())

    if not body:
        return PayloadLimitResult.success(policy_version=active.policy_version)

    byte_result = validate_request_bytes(body, active)
    if not byte_result.ok:
        return byte_result

    material = parsed
    if material is None:
        try:
            material = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            # Malformed JSON is owned by Slice 7.3; do not invent parser errors here.
            return PayloadLimitResult.success(policy_version=active.policy_version)

    return validate_json_structure(material, active)


def validate_request_bytes(
    body: bytes,
    policy: PayloadLimitPolicy,
) -> PayloadLimitResult:
    if len(body) > policy.max_request_bytes:
        return PayloadLimitResult.rejected(
            error_code=ERROR_PAYLOAD_TOO_LARGE,
            http_status=HTTP_PAYLOAD_TOO_LARGE,
            limit_name="max_request_bytes",
            policy_version=policy.policy_version,
        )
    return PayloadLimitResult.success(policy_version=policy.policy_version)


def validate_json_structure(
    value: Any,
    policy: PayloadLimitPolicy,
) -> PayloadLimitResult:
    """Walk JSON-like structures with deterministic limit precedence.

    Precedence (first match wins, stable for identical trees):
    1. depth
    2. traversal complexity
    3. array length
    4. object property count
    5. string length
    """

    traversal = 0

    def walk(node: Any, depth: int) -> PayloadLimitResult | None:
        nonlocal traversal
        traversal += 1
        if depth > policy.max_json_depth:
            return PayloadLimitResult.rejected(
                error_code=ERROR_PAYLOAD_TOO_DEEP,
                http_status=HTTP_PAYLOAD_TOO_LARGE,
                limit_name="max_json_depth",
                policy_version=policy.policy_version,
            )
        if traversal > policy.max_traversal_count:
            return PayloadLimitResult.rejected(
                error_code=ERROR_PAYLOAD_COMPLEXITY_LIMIT,
                http_status=HTTP_PAYLOAD_TOO_LARGE,
                limit_name="max_traversal_count",
                policy_version=policy.policy_version,
            )

        if isinstance(node, list):
            if len(node) > policy.max_array_length:
                return PayloadLimitResult.rejected(
                    error_code=ERROR_PAYLOAD_ARRAY_LIMIT,
                    http_status=HTTP_PAYLOAD_TOO_LARGE,
                    limit_name="max_array_length",
                    policy_version=policy.policy_version,
                )
            for item in node:
                failed = walk(item, depth + 1)
                if failed is not None:
                    return failed
            return None

        if isinstance(node, dict):
            if len(node) > policy.max_object_properties:
                return PayloadLimitResult.rejected(
                    error_code=ERROR_PAYLOAD_OBJECT_LIMIT,
                    http_status=HTTP_PAYLOAD_TOO_LARGE,
                    limit_name="max_object_properties",
                    policy_version=policy.policy_version,
                )
            # Deterministic key order for walk / first-failure stability.
            for key in sorted(node, key=str):
                if isinstance(key, str) and len(key) > policy.max_string_length:
                    return PayloadLimitResult.rejected(
                        error_code=ERROR_PAYLOAD_STRING_LIMIT,
                        http_status=HTTP_PAYLOAD_TOO_LARGE,
                        limit_name="max_string_length",
                        policy_version=policy.policy_version,
                    )
                failed = walk(node[key], depth + 1)
                if failed is not None:
                    return failed
            return None

        if isinstance(node, str) and len(node) > policy.max_string_length:
            return PayloadLimitResult.rejected(
                error_code=ERROR_PAYLOAD_STRING_LIMIT,
                http_status=HTTP_PAYLOAD_TOO_LARGE,
                limit_name="max_string_length",
                policy_version=policy.policy_version,
            )
        return None

    # Root occupies depth 1.
    failed = walk(value, 1)
    if failed is not None:
        return failed
    return PayloadLimitResult.success(policy_version=policy.policy_version)
