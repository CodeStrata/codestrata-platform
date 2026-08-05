"""Deterministic, non-reversible Data Lake object identifiers (Slice 8.1)."""

from __future__ import annotations

import hashlib

LAKE_OBJECT_ID_PREFIX = "lake-object:"
# Quarantine objects use a distinct prefix (Slice 8.9); filename extraction
# accepts both so ``build_quarantine_object_key`` can share this helper.
QUARANTINE_OBJECT_ID_PREFIX = "quarantine-object:"
LAKE_OBJECT_ID_HEX_LENGTH = 24

_OPAQUE_OBJECT_ID_PREFIXES: tuple[str, ...] = (
    LAKE_OBJECT_ID_PREFIX,
    QUARANTINE_OBJECT_ID_PREFIX,
)


class LakeIdentifierError(ValueError):
    """Raised when a lake object id cannot be derived safely."""


def build_lake_object_id(
    policy_token: str,
    event_stream: str,
    source_schema_version: str,
    event_key: str,
) -> str:
    """Build ``lake-object:{sha256[:24]}`` from bounded identity material only.

    Material is limited to ``policy_token``, ``event_stream``,
    ``source_schema_version``, and ``event_key``. No request id, IP address,
    timestamp, or random UUID is ever included, so an identical logical event
    always maps to the same object id (required for idempotent replay
    detection at the store).
    """

    if not policy_token or not policy_token.strip():
        raise LakeIdentifierError("policy_token is required")
    if not event_stream or not event_stream.strip():
        raise LakeIdentifierError("event_stream is required")
    if not source_schema_version or not source_schema_version.strip():
        raise LakeIdentifierError("source_schema_version is required")
    if not event_key or not event_key.strip():
        raise LakeIdentifierError("event_key is required")

    material = "|".join(
        (
            policy_token.strip(),
            event_stream.strip(),
            source_schema_version.strip(),
            event_key.strip(),
        )
    )
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return f"{LAKE_OBJECT_ID_PREFIX}{digest[:LAKE_OBJECT_ID_HEX_LENGTH]}"


def build_opaque_object_filename(object_id: str) -> str:
    """Return ``{hex}.json`` — the opaque on-disk filename for a lake/quarantine id.

    Accepts ``lake-object:`` (accepted writes) and ``quarantine-object:``
    (Slice 8.9 quarantine writes). The filename intentionally carries no
    stream, schema, date, or event identity — only the opaque digest fragment.
    """

    if not object_id:
        raise LakeIdentifierError("invalid lake object id: missing prefix")
    for prefix in _OPAQUE_OBJECT_ID_PREFIXES:
        if object_id.startswith(prefix):
            hex_part = object_id[len(prefix) :]
            if not hex_part or any(ch not in "0123456789abcdef" for ch in hex_part):
                raise LakeIdentifierError("invalid lake object id: non-hex body")
            return f"{hex_part}.json"
    raise LakeIdentifierError("invalid lake object id: missing prefix")
