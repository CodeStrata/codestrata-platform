"""Hive-style S3 key construction for Community Data Lake objects (Slice 8.1).

Object keys intentionally exclude any raw identity material — event keys,
safe event references, installation ids, request ids, IP addresses, or
filesystem paths never appear in a key. Only the opaque lake-object hex
filename (see :mod:`.identifiers`) identifies an object on disk.
"""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.envelopes import DataLakeEnvelope
from codestrata_platform.community_cloud_api.data_lake.identifiers import (
    build_opaque_object_filename,
)
from codestrata_platform.community_cloud_api.data_lake.validation import (
    validate_event_stream,
    validate_partition_date,
    validate_quarantine_reason,
    validate_schema_version,
)

ACCEPTED_ROOT = "raw"
QUARANTINE_ROOT = "quarantine"

# Defense-in-depth: even though every component is separately validated
# against an allowlist/regex before key construction, the assembled key is
# re-scanned for these substrings before it is ever returned to a caller.
_FORBIDDEN_KEY_SUBSTRINGS: tuple[str, ...] = (
    "/users/",
    "/home/",
    "/tmp/",
    "event:",
    "evt-",
    "installation",
    "request_id",
    "ip_address",
    "client_ip",
    "..",
)


class PartitionKeyError(ValueError):
    """Raised when a Data Lake object key cannot be built safely."""


def build_accepted_object_key(
    envelope: DataLakeEnvelope,
    lake_object_id: str,
    *,
    hive_style: bool = True,
) -> str:
    """Build the accepted-prefix object key for a validated envelope.

    Example (hive style): ``raw/stream=telemetry/schema_version=1.0/
    year=2026/month=08/day=03/{opaque}.json``.
    """

    stream = validate_event_stream(envelope.event_stream)
    schema_version = validate_schema_version(envelope.source_schema_version)
    year, month, day = validate_partition_date(
        envelope.accepted_year, envelope.accepted_month, envelope.accepted_day
    )
    filename = build_opaque_object_filename(lake_object_id)

    if hive_style:
        key = (
            f"{ACCEPTED_ROOT}/stream={stream}/schema_version={schema_version}/"
            f"year={year}/month={month}/day={day}/{filename}"
        )
    else:
        key = f"{ACCEPTED_ROOT}/{stream}/{schema_version}/{year}/{month}/{day}/{filename}"

    assert_key_excludes_identity_material(key)
    return key


def build_quarantine_object_key(
    reason: str,
    year: str,
    month: str,
    day: str,
    lake_object_id: str,
    *,
    hive_style: bool = True,
) -> str:
    """Build the quarantine-prefix object key for a rejected/unsafe event."""

    reason_code = validate_quarantine_reason(reason)
    y, m, d = validate_partition_date(year, month, day)
    filename = build_opaque_object_filename(lake_object_id)

    if hive_style:
        key = (
            f"{QUARANTINE_ROOT}/reason={reason_code}/year={y}/month={m}/day={d}/{filename}"
        )
    else:
        key = f"{QUARANTINE_ROOT}/{reason_code}/{y}/{m}/{d}/{filename}"

    assert_key_excludes_identity_material(key)
    return key


def assert_key_excludes_identity_material(key: str) -> None:
    """Raise :class:`PartitionKeyError` when a key carries raw identity material."""

    if not key or "\x00" in key:
        raise PartitionKeyError("object key must be a non-empty, printable string")
    lowered = key.lower()
    for token in _FORBIDDEN_KEY_SUBSTRINGS:
        if token in lowered:
            raise PartitionKeyError(f"object key contains forbidden material: {token!r}")
