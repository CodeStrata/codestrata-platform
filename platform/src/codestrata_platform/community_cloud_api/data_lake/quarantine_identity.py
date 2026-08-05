"""Deterministic quarantine object identifiers (Slice 8.9).

Identity deliberately **excludes** ``detected_at`` and partition date
(``year``/``month``/``day``): the same logical rejection produces the same
``quarantine-object:`` id even when quarantined on different calendar days.
The object *key* still includes the date partition for operational listing;
only the opaque hex filename is identity-stable across dates.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Protocol

from codestrata_platform.community_cloud_api.data_lake.identifiers import (
    LAKE_OBJECT_ID_HEX_LENGTH,
    QUARANTINE_OBJECT_ID_PREFIX,
)

if TYPE_CHECKING:
    from codestrata_platform.community_cloud_api.data_lake.quarantine_models import (
        QuarantineRecord,
    )

# Re-export for quarantine call sites; canonical definition lives in identifiers.
__all__ = [
    "QUARANTINE_OBJECT_ID_PREFIX",
    "QUARANTINE_REFERENCE_PREFIX",
    "QuarantineIdentifierError",
    "build_quarantine_object_id",
    "opaque_quarantine_hex",
    "quarantine_reference_from_object_id",
]

QUARANTINE_REFERENCE_PREFIX = "qz-"
_REFERENCE_HEX_LENGTH = 16


class QuarantineIdentifierError(ValueError):
    """Raised when a quarantine object id cannot be derived safely."""


class _QuarantineIdentityMaterial(Protocol):
    quarantine_schema_version: str
    quarantine_reason: str
    validation_stage: str
    event_stream: str | None
    safe_event_reference: str | None
    safe_object_reference: str | None
    diagnostic_codes: tuple[str, ...]


def build_quarantine_object_id(
    record_or_material: _QuarantineIdentityMaterial | QuarantineRecord,
    *,
    policy_token: str,
) -> str:
    """Build ``quarantine-object:{sha256[:24]}`` from bounded identity material.

    Material is limited to policy token, schema version, reason, validation
    stage, optional event stream / safe references, and sorted diagnostic
    codes. Never includes ``detected_at``, partition date, raw body,
    ``event_id``, ``installation_id``, ``request_id``, IP, exception text,
    or a random UUID.
    """

    if not policy_token or not str(policy_token).strip():
        raise QuarantineIdentifierError("policy_token is required")

    material = "|".join(
        (
            policy_token.strip(),
            (record_or_material.quarantine_schema_version or "").strip(),
            (record_or_material.quarantine_reason or "").strip(),
            (record_or_material.validation_stage or "").strip(),
            (record_or_material.event_stream or "").strip(),
            (record_or_material.safe_event_reference or "").strip(),
            (record_or_material.safe_object_reference or "").strip(),
            ",".join(record_or_material.diagnostic_codes),
        )
    )
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return f"{QUARANTINE_OBJECT_ID_PREFIX}{digest[:LAKE_OBJECT_ID_HEX_LENGTH]}"


def quarantine_reference_from_object_id(object_id: str) -> str:
    """Derive opaque ``qz-{hex}`` from a ``quarantine-object:`` id."""

    if not object_id or not object_id.startswith(QUARANTINE_OBJECT_ID_PREFIX):
        raise QuarantineIdentifierError("invalid quarantine object id: missing prefix")
    hex_part = object_id[len(QUARANTINE_OBJECT_ID_PREFIX) :]
    if not hex_part or any(ch not in "0123456789abcdef" for ch in hex_part):
        raise QuarantineIdentifierError("invalid quarantine object id: non-hex body")
    return f"{QUARANTINE_REFERENCE_PREFIX}{hex_part[:_REFERENCE_HEX_LENGTH]}"


def opaque_quarantine_hex(object_id: str) -> str:
    """Return the hex fragment of a ``quarantine-object:`` id."""

    if not object_id or not object_id.startswith(QUARANTINE_OBJECT_ID_PREFIX):
        raise QuarantineIdentifierError("invalid quarantine object id: missing prefix")
    hex_part = object_id[len(QUARANTINE_OBJECT_ID_PREFIX) :]
    if (
        len(hex_part) != LAKE_OBJECT_ID_HEX_LENGTH
        or any(ch not in "0123456789abcdef" for ch in hex_part)
    ):
        raise QuarantineIdentifierError("invalid quarantine object id: non-hex body")
    return hex_part
