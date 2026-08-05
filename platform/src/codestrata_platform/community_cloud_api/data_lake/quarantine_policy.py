"""Versioned quarantine policy for Community Data Lake malformed-event records (Slice 8.9).

Retention alignment with the lake policy's ``quarantine_retention_days`` (90)
is documented here for operators — this module does **not** duplicate OpenTofu
lifecycle HCL. Quarantine persistence is implemented but unwired from
endpoints / ``app.py`` / ``deployment/wiring.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.enums import (
    EventStream,
    QuarantineReasonCode,
    QuarantineValidationStage,
)

COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_ID = "community-data-lake-quarantine-policy"
COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_VERSION = "1.0"
COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_URN = (
    f"{COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_ID}:{COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_VERSION}"
)

# Aligns with CommunityDataLakePolicy.quarantine_retention_days default and
# infrastructure modules/community-data-lake lifecycle — documented only.
_DEFAULT_RETENTION_DAYS_REFERENCE = 90

_ALL_REASON_CODES: frozenset[str] = frozenset(item.value for item in QuarantineReasonCode)
_ALL_VALIDATION_STAGES: frozenset[str] = frozenset(
    item.value for item in QuarantineValidationStage
)
_ALL_EVENT_STREAMS: frozenset[str] = frozenset(item.value for item in EventStream)

# Empty / unknown stream markers when the originating stream cannot be known
# safely (e.g. request never reached stream classification).
_OPTIONAL_STREAM_MARKERS: frozenset[str] = frozenset({"", "unknown"})

QUARANTINE_S3_METADATA_ALLOWLIST: frozenset[str] = frozenset(
    {
        "codestrata-content-sha256",
        "codestrata-quarantine-schema",
        "codestrata-quarantine-reason",
        "codestrata-object-id",
    }
)

FORBIDDEN_QUARANTINE_FIELD_NAMES: frozenset[str] = frozenset(
    {
        "body",
        "raw_body",
        "payload",
        "headers",
        "authorization",
        "cookie",
        "cookies",
        "token",
        "credential",
        "credentials",
        "secret",
        "password",
        "api_key",
        "connection_string",
        "private_key",
        "event_id",
        "installation_id",
        "request_id",
        "ip",
        "ip_address",
        "client_ip",
        "remote_addr",
        "principal",
        "repository",
        "project",
        "path",
        "file",
        "source",
        "prompt",
        "response",
        "exception",
        "traceback",
        "stack",
        "stack_trace",
        "aws_request_id",
        "bucket",
        "object_key",
        "etag",
        "version_id",
        "access_key",
        "aws_secret",
        "bearer",
    }
)

ALLOWED_QUARANTINE_DIAGNOSTIC_CODES: frozenset[str] = frozenset(
    {
        "missing_required_field",
        "unsupported_version",
        "unsupported_envelope_schema",
        "unsupported_source_schema",
        "unsupported_source_policy",
        "invalid_enum",
        "unsafe_field_name",
        "unsafe_value_shape",
        "size_limit_exceeded",
        "checksum_mismatch",
        "metadata_mismatch",
        "key_validation_failed",
        "conditional_write_conflict",
        "storage_dependency_unavailable",
        "stream_mismatch",
        "stream_contract_mismatch",
        "invalid_payload",
        "invalid_partition",
        "invalid_storage_object",
        "malformed_stored_object",
        "serialization_failure",
        "storage_rejected",
        "storage_key_failure",
        "partition_invalid",
        "envelope_too_large",
        "unsafe_payload",
        "invalid_envelope",
    }
)

_DEFAULT_LIMITATIONS: tuple[str, ...] = (
    "quarantine_unwired_from_endpoints",
    "no_raw_http_body_or_headers_persisted",
    "retention_days_reference_only_not_hcl",
    "no_exactly_once_delivery_guarantee",
)


@dataclass(frozen=True, slots=True)
class CommunityDataLakeQuarantinePolicy:
    """Deterministic policy governing quarantine record shape and metadata."""

    policy_id: str = COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_ID
    policy_version: str = COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_VERSION
    supported_quarantine_schema_versions: frozenset[str] = frozenset({"1.0"})
    allowed_reason_codes: frozenset[str] = _ALL_REASON_CODES
    allowed_validation_stages: frozenset[str] = _ALL_VALIDATION_STAGES
    max_diagnostic_codes: int = 16
    max_diagnostic_code_length: int = 64
    max_limitations: int = 32
    max_serialized_record_bytes: int = 8192
    allowed_event_streams: frozenset[str] = frozenset(
        _ALL_EVENT_STREAMS | _OPTIONAL_STREAM_MARKERS
    )
    allow_safe_event_reference: bool = True
    allow_safe_object_reference: bool = True
    s3_metadata_allowlist: frozenset[str] = QUARANTINE_S3_METADATA_ALLOWLIST
    forbidden_field_names: frozenset[str] = FORBIDDEN_QUARANTINE_FIELD_NAMES
    allowed_diagnostic_codes: frozenset[str] = ALLOWED_QUARANTINE_DIAGNOSTIC_CODES
    retention_days_reference: int = _DEFAULT_RETENTION_DAYS_REFERENCE
    limitations: tuple[str, ...] = _DEFAULT_LIMITATIONS

    def __post_init__(self) -> None:
        self.validate()
        object.__setattr__(self, "limitations", tuple(sorted(set(self.limitations))))

    @property
    def policy_token(self) -> str:
        return f"{self.policy_id}:{self.policy_version}"

    @property
    def policy_urn(self) -> str:
        return f"{self.policy_id}:{self.policy_version}"

    def validate(self) -> None:
        if self.policy_id != COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_ID:
            raise ValueError("unsupported quarantine policy id")
        if self.policy_version != COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_VERSION:
            raise ValueError("unsupported quarantine policy version")
        if "1.0" not in self.supported_quarantine_schema_versions:
            raise ValueError("supported_quarantine_schema_versions must include '1.0'")
        if not self.allowed_reason_codes:
            raise ValueError("allowed_reason_codes must not be empty")
        if not self.allowed_validation_stages:
            raise ValueError("allowed_validation_stages must not be empty")
        if self.max_diagnostic_codes <= 0:
            raise ValueError("max_diagnostic_codes must be positive")
        if self.max_diagnostic_code_length <= 0:
            raise ValueError("max_diagnostic_code_length must be positive")
        if self.max_limitations <= 0:
            raise ValueError("max_limitations must be positive")
        if self.max_serialized_record_bytes < 256:
            raise ValueError("max_serialized_record_bytes too small")
        if not self.s3_metadata_allowlist:
            raise ValueError("s3_metadata_allowlist must not be empty")
        if not (7 <= self.retention_days_reference <= 365):
            raise ValueError("retention_days_reference out of documented bounds [7, 365]")

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "allow_safe_event_reference": self.allow_safe_event_reference,
            "allow_safe_object_reference": self.allow_safe_object_reference,
            "allowed_diagnostic_codes": sorted(self.allowed_diagnostic_codes),
            "allowed_event_streams": sorted(self.allowed_event_streams),
            "allowed_reason_codes": sorted(self.allowed_reason_codes),
            "allowed_validation_stages": sorted(self.allowed_validation_stages),
            "forbidden_field_names": sorted(self.forbidden_field_names),
            "limitations": list(self.limitations),
            "max_diagnostic_code_length": self.max_diagnostic_code_length,
            "max_diagnostic_codes": self.max_diagnostic_codes,
            "max_limitations": self.max_limitations,
            "max_serialized_record_bytes": self.max_serialized_record_bytes,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "retention_days_reference": self.retention_days_reference,
            "s3_metadata_allowlist": sorted(self.s3_metadata_allowlist),
            "supported_quarantine_schema_versions": sorted(
                self.supported_quarantine_schema_versions
            ),
        }


def default_quarantine_policy() -> CommunityDataLakeQuarantinePolicy:
    return CommunityDataLakeQuarantinePolicy()
