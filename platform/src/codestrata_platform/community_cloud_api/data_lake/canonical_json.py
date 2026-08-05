"""Canonical raw-JSON serialization for immutable Data Lake storage (Slice 8.2).

This is the *storage authority* serialization: it mirrors the sorting and
number/NaN rules of
:func:`codestrata_platform.community_cloud_api.serialization.to_stable_json_dict`,
but is intentionally a separate implementation with no import dependency on
the HTTP serialization module. The storage form differs from the HTTP form
(:func:`~codestrata_platform.community_cloud_api.serialization.dumps_stable`)
in one deliberate way: it has **no trailing newline** — the trailing newline
in the HTTP helper is a wire-format convenience, not part of the durable
byte-for-byte content whose SHA-256 digest is the storage identity.
"""

from __future__ import annotations

import base64
import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

CONTENT_TYPE_APPLICATION_JSON = "application/json"
CONTENT_DIGEST_PREFIX = "sha256:"
_SHA256_HEX_LENGTH = 64


class CanonicalJsonError(ValueError):
    """Raised when an envelope cannot be serialized to canonical storage JSON."""


@dataclass(frozen=True, slots=True)
class CanonicalRawJson:
    """The exact, immutable bytes that will be written to object storage."""

    data: bytes
    content_sha256: str
    content_length: int


def to_canonical_json_value(value: Any) -> Any:
    """Recursively normalize ``value`` into a sorted-map JSON-safe structure.

    Mirrors the rules of ``serialization.to_stable_json_dict``: map keys are
    sorted, list order is preserved, and NaN/Infinity floats are rejected.
    Kept as an independent implementation on purpose — the storage boundary
    must not depend on the HTTP response serialization module.
    """

    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise CanonicalJsonError("NaN/Infinity are not permitted in canonical storage JSON")
        return value
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        return {str(key): to_canonical_json_value(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [to_canonical_json_value(item) for item in value]
    if hasattr(value, "to_stable_dict") and callable(value.to_stable_dict):
        return to_canonical_json_value(value.to_stable_dict())
    raise CanonicalJsonError(f"unsupported canonical JSON value type: {type(value)!r}")


def serialize_canonical_raw_json(envelope: Any) -> CanonicalRawJson:
    """Serialize ``envelope.to_stable_dict()`` into canonical storage bytes.

    Encoding is UTF-8, sorted keys, compact separators, ASCII-escaped, no
    NaN/Infinity, and — unlike the HTTP ``dumps_stable`` helper — **no
    trailing newline**, since these bytes are the durable object content
    whose SHA-256 digest is the write's idempotency identity.
    """

    stable = envelope.to_stable_dict()
    if not isinstance(stable, Mapping):
        raise CanonicalJsonError("canonical storage JSON root must be a JSON object")
    canonical_value = to_canonical_json_value(stable)
    if not isinstance(canonical_value, dict):
        raise CanonicalJsonError("canonical storage JSON root must be a JSON object")
    text = json.dumps(
        canonical_value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    data = text.encode("utf-8")
    content_sha256 = CONTENT_DIGEST_PREFIX + hashlib.sha256(data).hexdigest()
    return CanonicalRawJson(data=data, content_sha256=content_sha256, content_length=len(data))


def content_digest_hex(digest: str) -> str:
    """Strip the ``sha256:`` prefix, raising :class:`CanonicalJsonError` if absent."""

    if not digest or not digest.startswith(CONTENT_DIGEST_PREFIX):
        raise CanonicalJsonError("digest missing 'sha256:' prefix")
    hex_part = digest[len(CONTENT_DIGEST_PREFIX) :]
    if len(hex_part) != _SHA256_HEX_LENGTH:
        raise CanonicalJsonError("digest hex fragment has invalid length")
    return hex_part


def digest_matches(a: str, b: str) -> bool:
    """Return ``True`` only when both digests are well-formed and equal."""

    try:
        return content_digest_hex(a).lower() == content_digest_hex(b).lower()
    except CanonicalJsonError:
        return False


def checksum_sha256_b64(canonical_bytes: bytes) -> str:
    """Base64 of the raw 32-byte SHA-256 digest, for the S3 ``ChecksumSHA256`` param."""

    raw_digest = hashlib.sha256(canonical_bytes).digest()
    return base64.b64encode(raw_digest).decode("ascii")


def validate_utf8_json_object_bytes(data: bytes) -> dict[str, Any]:
    """Decode ``data`` as UTF-8 JSON and require an object (map) root."""

    try:
        text = bytes(data).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CanonicalJsonError("stored bytes are not valid UTF-8") from exc
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CanonicalJsonError("stored bytes are not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise CanonicalJsonError("stored JSON root must be an object")
    return parsed
