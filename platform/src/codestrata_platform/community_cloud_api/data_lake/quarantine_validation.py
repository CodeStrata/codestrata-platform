"""Validate quarantine records against policy (Slice 8.9)."""

from __future__ import annotations

import re
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.quarantine_models import (
    COMMUNITY_DATA_LAKE_QUARANTINE_SCHEMA_VERSION,
    QuarantineRecord,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_policy import (
    CommunityDataLakeQuarantinePolicy,
    default_quarantine_policy,
)
from codestrata_platform.community_cloud_api.data_lake.validation import (
    validate_partition_date,
)

_DETECTED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_SCHEMA_VERSION_RE = re.compile(r"^[0-9]+(\.[0-9]+)*$")
_SAFE_EVENT_REF_RE = re.compile(r"^evt-[0-9a-zA-Z_-]{1,64}$")
_SAFE_OBJECT_REF_RE = re.compile(r"^lake-ref:[0-9a-f]{1,64}$")
_QUARANTINE_REF_RE = re.compile(r"^qz-[0-9a-f]{1,64}$")
_DIAGNOSTIC_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")

# Substrings that must never appear inside diagnostic code strings even if
# somehow allowlisted — defense in depth against credential-looking values.
_FORBIDDEN_DIAGNOSTIC_SUBSTRINGS: tuple[str, ...] = (
    "password",
    "secret",
    "token",
    "bearer",
    "authorization",
    "cookie",
    "api_key",
    "private_key",
    "credential",
    "akia",
    "cscc_v1_",
    "event:",
    "evt-",
    "installation",
    "request_id",
)


class QuarantineValidationError(ValueError):
    """Raised when a quarantine record fails policy validation."""


def _reject_forbidden_names(names: set[str], *, policy: CommunityDataLakeQuarantinePolicy) -> None:
    forbidden = policy.forbidden_field_names
    for name in names:
        lowered = name.lower().strip()
        if lowered in forbidden:
            raise QuarantineValidationError(f"forbidden quarantine field name: {name!r}")


def validate_quarantine_record(
    record: QuarantineRecord,
    *,
    quarantine_policy: CommunityDataLakeQuarantinePolicy | None = None,
) -> QuarantineRecord:
    """Validate ``record`` against ``quarantine_policy``; return ``record`` unchanged."""

    policy = quarantine_policy or default_quarantine_policy()
    policy.validate()

    _reject_forbidden_names(set(record.to_stable_dict()), policy=policy)

    if record.quarantine_schema_version not in policy.supported_quarantine_schema_versions:
        raise QuarantineValidationError(
            f"unsupported quarantine schema version: {record.quarantine_schema_version!r}"
        )
    if record.quarantine_schema_version != COMMUNITY_DATA_LAKE_QUARANTINE_SCHEMA_VERSION:
        raise QuarantineValidationError(
            f"unsupported quarantine schema version: {record.quarantine_schema_version!r}"
        )

    if record.quarantine_reason not in policy.allowed_reason_codes:
        raise QuarantineValidationError(
            f"unsupported quarantine reason: {record.quarantine_reason!r}"
        )
    if record.validation_stage not in policy.allowed_validation_stages:
        raise QuarantineValidationError(
            f"unsupported validation stage: {record.validation_stage!r}"
        )

    if not _DETECTED_AT_RE.match(record.detected_at or ""):
        raise QuarantineValidationError(f"invalid detected_at: {record.detected_at!r}")
    validate_partition_date(record.year, record.month, record.day)

    if not _QUARANTINE_REF_RE.match(record.quarantine_reference or ""):
        raise QuarantineValidationError(
            f"invalid quarantine_reference: {record.quarantine_reference!r}"
        )

    if record.event_stream is not None:
        stream = record.event_stream.strip()
        if stream not in policy.allowed_event_streams:
            raise QuarantineValidationError(f"unsupported event stream: {record.event_stream!r}")

    for field_name, value in (
        ("source_schema_version", record.source_schema_version),
        ("envelope_schema_version", record.envelope_schema_version),
    ):
        if value is not None:
            if not _SCHEMA_VERSION_RE.match(value.strip()):
                raise QuarantineValidationError(f"invalid {field_name}: {value!r}")

    if record.safe_event_reference is not None:
        if not policy.allow_safe_event_reference:
            raise QuarantineValidationError("safe_event_reference not allowed by policy")
        if not _SAFE_EVENT_REF_RE.match(record.safe_event_reference):
            raise QuarantineValidationError(
                f"invalid safe_event_reference: {record.safe_event_reference!r}"
            )

    if record.safe_object_reference is not None:
        if not policy.allow_safe_object_reference:
            raise QuarantineValidationError("safe_object_reference not allowed by policy")
        if not _SAFE_OBJECT_REF_RE.match(record.safe_object_reference):
            raise QuarantineValidationError(
                f"invalid safe_object_reference: {record.safe_object_reference!r}"
            )

    codes = record.diagnostic_codes
    if len(codes) != len(set(codes)):
        raise QuarantineValidationError("diagnostic_codes must be unique")
    if list(codes) != sorted(codes):
        raise QuarantineValidationError("diagnostic_codes must be sorted")
    if len(codes) > policy.max_diagnostic_codes:
        raise QuarantineValidationError("too many diagnostic_codes")
    for code in codes:
        if len(code) > policy.max_diagnostic_code_length:
            raise QuarantineValidationError("diagnostic code exceeds max length")
        if not _DIAGNOSTIC_CODE_RE.match(code):
            raise QuarantineValidationError(f"invalid diagnostic code shape: {code!r}")
        if code not in policy.allowed_diagnostic_codes:
            raise QuarantineValidationError(f"diagnostic code not allowlisted: {code!r}")
        lowered = code.lower()
        for token in _FORBIDDEN_DIAGNOSTIC_SUBSTRINGS:
            if token in lowered:
                raise QuarantineValidationError(
                    f"diagnostic code contains forbidden material: {token!r}"
                )

    limitations = record.limitations
    if len(limitations) > policy.max_limitations:
        raise QuarantineValidationError("too many limitations")
    if list(limitations) != sorted(set(limitations)):
        raise QuarantineValidationError("limitations must be sorted unique strings")
    for item in limitations:
        if not isinstance(item, str) or not item.strip():
            raise QuarantineValidationError("limitations entries must be non-blank strings")
        if len(item) > policy.max_diagnostic_code_length * 2:
            raise QuarantineValidationError("limitation entry exceeds max length")
        _reject_forbidden_names({item}, policy=policy)

    return record


def assert_no_forbidden_diagnostics_map(
    diagnostics: dict[str, Any] | None,
    *,
    quarantine_policy: CommunityDataLakeQuarantinePolicy | None = None,
) -> None:
    """Reject any free-form diagnostics map that uses forbidden field names."""

    if not diagnostics:
        return
    policy = quarantine_policy or default_quarantine_policy()
    _reject_forbidden_names(set(diagnostics), policy=policy)
    for key, value in diagnostics.items():
        if isinstance(value, dict):
            assert_no_forbidden_diagnostics_map(value, quarantine_policy=policy)
        elif isinstance(value, str):
            lowered = value.lower()
            for token in _FORBIDDEN_DIAGNOSTIC_SUBSTRINGS:
                if token in lowered and token in ("password", "secret", "bearer", "authorization"):
                    raise QuarantineValidationError(
                        f"diagnostic value contains forbidden material: {token!r}"
                    )
