"""Structural validation helpers for Data Lake identity and partition material."""

from __future__ import annotations

import re

from codestrata_platform.community_cloud_api.data_lake.enums import (
    EventStream,
    QuarantineReasonCode,
)

_SCHEMA_VERSION_RE = re.compile(r"^[0-9]+(\.[0-9]+)*$")
_YEAR_RE = re.compile(r"^[0-9]{4}$")
_MONTH_RE = re.compile(r"^(0[1-9]|1[0-2])$")
_DAY_RE = re.compile(r"^(0[1-9]|[12][0-9]|3[01])$")


class DataLakeValidationError(ValueError):
    """Raised when Data Lake identity or partition material is invalid."""


def validate_event_stream(value: str) -> str:
    text = (value or "").strip()
    allowed = {item.value for item in EventStream}
    if text not in allowed:
        raise DataLakeValidationError(f"unsupported event stream: {value!r}")
    return text


def validate_schema_version(value: str) -> str:
    text = (value or "").strip()
    if not text or not _SCHEMA_VERSION_RE.match(text):
        raise DataLakeValidationError(f"invalid schema version: {value!r}")
    return text


def validate_partition_date(year: str, month: str, day: str) -> tuple[str, str, str]:
    y = (year or "").strip()
    m = (month or "").strip()
    d = (day or "").strip()
    if not _YEAR_RE.match(y):
        raise DataLakeValidationError(f"invalid partition year: {year!r}")
    if not _MONTH_RE.match(m):
        raise DataLakeValidationError(f"invalid partition month: {month!r}")
    if not _DAY_RE.match(d):
        raise DataLakeValidationError(f"invalid partition day: {day!r}")
    return y, m, d


def validate_quarantine_reason(value: str) -> str:
    text = (value or "").strip()
    allowed = {item.value for item in QuarantineReasonCode}
    if text not in allowed:
        raise DataLakeValidationError(f"unsupported quarantine reason: {value!r}")
    return text


def validate_retention_bounds(
    *,
    accepted_retention_days: int,
    quarantine_retention_days: int,
    accepted_min_days: int = 30,
    accepted_max_days: int = 2555,
    quarantine_min_days: int = 7,
    quarantine_max_days: int = 365,
) -> None:
    if not (accepted_min_days <= accepted_retention_days <= accepted_max_days):
        raise DataLakeValidationError(
            f"accepted_retention_days out of bounds [{accepted_min_days}, {accepted_max_days}]"
        )
    if not (quarantine_min_days <= quarantine_retention_days <= quarantine_max_days):
        raise DataLakeValidationError(
            "quarantine_retention_days out of bounds "
            f"[{quarantine_min_days}, {quarantine_max_days}]"
        )


def reject_mutable_overwrite(
    *,
    existing_fingerprint: str | None,
    incoming_fingerprint: str | None,
) -> bool:
    """Return ``True`` when a write must be rejected as a mutable overwrite.

    Same object key + same content fingerprint is an idempotent replay (not a
    rejection). Same object key + a different content fingerprint is a
    conflict that must never silently overwrite the original object.
    """

    if existing_fingerprint is None:
        return False
    return existing_fingerprint != incoming_fingerprint
