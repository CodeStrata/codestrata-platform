"""Versioned quarantine record model for malformed Community Data Lake events (Slice 8.9).

A :class:`QuarantineRecord` is the privacy-safe, bounded document persisted
under ``quarantine/``. It never carries raw HTTP bodies, headers,
Authorization, cookies, IPs, ``event_id``, ``installation_id``, prompts,
``source``, credentials, payload digests of rejected material, bucket names,
or object keys.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.accepted_clock import (
    AcceptanceClock,
    FixedAcceptanceClock,
    SystemAcceptanceClock,
    format_accepted_at,
    partition_components,
    partition_date_from_accepted_at,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_identity import (
    QUARANTINE_REFERENCE_PREFIX,
    build_quarantine_object_id,
    quarantine_reference_from_object_id,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_policy import (
    CommunityDataLakeQuarantinePolicy,
    default_quarantine_policy,
)

COMMUNITY_DATA_LAKE_QUARANTINE_SCHEMA_VERSION = "1.0"

# Re-export clocks so builders / tests can import from one place.
__all__ = [
    "COMMUNITY_DATA_LAKE_QUARANTINE_SCHEMA_VERSION",
    "QuarantineRecord",
    "build_quarantine_record",
    "FixedAcceptanceClock",
    "SystemAcceptanceClock",
]


@dataclass(frozen=True, slots=True)
class QuarantineRecord:
    """Bounded, privacy-safe quarantine document (schema ``1.0``)."""

    quarantine_reason: str
    validation_stage: str
    quarantine_reference: str
    detected_at: str
    year: str
    month: str
    day: str
    quarantine_schema_version: str = COMMUNITY_DATA_LAKE_QUARANTINE_SCHEMA_VERSION
    event_stream: str | None = None
    source_schema_version: str | None = None
    envelope_schema_version: str | None = None
    safe_event_reference: str | None = None
    safe_object_reference: str | None = None
    diagnostic_codes: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "day": self.day,
            "detected_at": self.detected_at,
            "diagnostic_codes": list(self.diagnostic_codes),
            "limitations": list(self.limitations),
            "month": self.month,
            "quarantine_reason": self.quarantine_reason,
            "quarantine_reference": self.quarantine_reference,
            "quarantine_schema_version": self.quarantine_schema_version,
            "validation_stage": self.validation_stage,
            "year": self.year,
        }
        if self.envelope_schema_version is not None:
            payload["envelope_schema_version"] = self.envelope_schema_version
        if self.event_stream is not None:
            payload["event_stream"] = self.event_stream
        if self.safe_event_reference is not None:
            payload["safe_event_reference"] = self.safe_event_reference
        if self.safe_object_reference is not None:
            payload["safe_object_reference"] = self.safe_object_reference
        if self.source_schema_version is not None:
            payload["source_schema_version"] = self.source_schema_version
        return {key: payload[key] for key in sorted(payload)}


def _normalize_diagnostic_codes(codes: Iterable[str] | None) -> tuple[str, ...]:
    if not codes:
        return ()
    return tuple(sorted({str(code).strip() for code in codes if str(code).strip()}))


def build_quarantine_record(
    *,
    quarantine_reason: str,
    validation_stage: str,
    clock: AcceptanceClock | None = None,
    quarantine_policy: CommunityDataLakeQuarantinePolicy | None = None,
    event_stream: str | None = None,
    source_schema_version: str | None = None,
    envelope_schema_version: str | None = None,
    safe_event_reference: str | None = None,
    safe_object_reference: str | None = None,
    diagnostic_codes: Iterable[str] | None = None,
    limitations: Iterable[str] | None = None,
    year: str | None = None,
    month: str | None = None,
    day: str | None = None,
    detected_at: str | None = None,
    quarantine_reference: str | None = None,
) -> QuarantineRecord:
    """Build a :class:`QuarantineRecord`, filling ``detected_at`` / date from ``clock``.

    ``quarantine_reference`` defaults to ``qz-{hex}`` derived from the
    deterministic quarantine object id (identity excludes date / detected_at).
    """

    policy = quarantine_policy or default_quarantine_policy()
    active_clock = clock or SystemAcceptanceClock()
    if detected_at is None:
        now = active_clock.now_utc()
        if not isinstance(now, datetime):  # pragma: no cover - protocol contract
            raise TypeError("AcceptanceClock.now_utc must return datetime")
        detected_at = format_accepted_at(now)
    if year is None or month is None or day is None:
        partition_date = partition_date_from_accepted_at(detected_at)
        derived_year, derived_month, derived_day = partition_components(partition_date)
        year = year or derived_year
        month = month or derived_month
        day = day or derived_day

    normalized_codes = _normalize_diagnostic_codes(diagnostic_codes)
    normalized_limitations = tuple(
        sorted({str(item).strip() for item in (limitations or ()) if str(item).strip()})
    )

    # Provisional record for identity — reference filled after id derivation.
    provisional = QuarantineRecord(
        quarantine_reason=quarantine_reason,
        validation_stage=validation_stage,
        quarantine_reference=quarantine_reference or f"{QUARANTINE_REFERENCE_PREFIX}pending",
        detected_at=detected_at,
        year=year,
        month=month,
        day=day,
        event_stream=event_stream,
        source_schema_version=source_schema_version,
        envelope_schema_version=envelope_schema_version,
        safe_event_reference=safe_event_reference,
        safe_object_reference=safe_object_reference,
        diagnostic_codes=normalized_codes,
        limitations=normalized_limitations,
    )
    object_id = build_quarantine_object_id(provisional, policy_token=policy.policy_token)
    reference = quarantine_reference or quarantine_reference_from_object_id(object_id)
    return QuarantineRecord(
        quarantine_reason=provisional.quarantine_reason,
        validation_stage=provisional.validation_stage,
        quarantine_reference=reference,
        detected_at=provisional.detected_at,
        year=provisional.year,
        month=provisional.month,
        day=provisional.day,
        event_stream=provisional.event_stream,
        source_schema_version=provisional.source_schema_version,
        envelope_schema_version=provisional.envelope_schema_version,
        safe_event_reference=provisional.safe_event_reference,
        safe_object_reference=provisional.safe_object_reference,
        diagnostic_codes=provisional.diagnostic_codes,
        limitations=provisional.limitations,
    )
