"""Deterministic payload fingerprints for conflicting-retry detection."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from codestrata_platform.community_cloud_api.event_identity.models import (
    CommunityEventIdentityPolicy,
)
from codestrata_platform.community_cloud_api.validation.sanitization import (
    contains_secret_like_value,
)


class FingerprintError(ValueError):
    """Raised when a payload cannot be fingerprinted safely."""


def compute_payload_fingerprint(
    payload: Mapping[str, Any],
    *,
    policy: CommunityEventIdentityPolicy | None = None,
) -> str:
    """Return ``fp:{sha256}`` over canonical JSON after exclusions.

    Hashes provide deterministic content identity only — not encryption and not
    a substitute for rejecting secret-like values before hashing.
    """

    active = policy or CommunityEventIdentityPolicy.default()
    if not isinstance(payload, Mapping):
        raise FingerprintError("payload must be a mapping")
    filtered = _strip_excluded(dict(payload), excluded=set(active.fingerprint_excluded_fields))
    _assert_no_secrets(filtered)
    canonical = _canonical_json(filtered)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"fp:{digest}"


def _strip_excluded(value: Any, *, excluded: set[str]) -> Any:
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key in sorted(value, key=str):
            name = str(key)
            if name in excluded:
                continue
            out[name] = _strip_excluded(value[key], excluded=excluded)
        return out
    if isinstance(value, list):
        # List order is semantic and preserved.
        return [_strip_excluded(item, excluded=excluded) for item in value]
    if isinstance(value, tuple):
        return [_strip_excluded(item, excluded=excluded) for item in value]
    return value


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _assert_no_secrets(value: Any) -> None:
    if isinstance(value, str):
        if contains_secret_like_value(value):
            raise FingerprintError("secret_like_value")
        return
    if isinstance(value, Mapping):
        for key in sorted(value, key=str):
            if isinstance(key, str) and contains_secret_like_value(key):
                raise FingerprintError("secret_like_value")
            _assert_no_secrets(value[key])
        return
    if isinstance(value, list):
        for item in value:
            _assert_no_secrets(item)
        return
    if value is None or isinstance(value, (bool, int)):
        return
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise FingerprintError("unsupported_float")
        return
    raise FingerprintError(f"unsupported_type:{type(value).__name__}")
