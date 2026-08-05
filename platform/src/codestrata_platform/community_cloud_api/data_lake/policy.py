"""Community Data Lake storage policy (Slice 8.1).

The defaults below are product-policy defaults and require review before any
production rollout (retention windows, versioning, lifecycle rules). Initial
encryption is SSE-S3; a possible future slice may migrate to SSE-KMS without
changing the envelope schema or object-key format defined in this package.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.constants import (
    COMMUNITY_DATA_LAKE_ENVELOPE_SCHEMA_VERSION,
    COMMUNITY_DATA_LAKE_POLICY_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.enums import (
    EncryptionMode,
    EventStream,
)

COMMUNITY_DATA_LAKE_POLICY_ID = "community-data-lake-policy"
COMMUNITY_DATA_LAKE_POLICY_URN = (
    f"{COMMUNITY_DATA_LAKE_POLICY_ID}:{COMMUNITY_DATA_LAKE_POLICY_VERSION}"
)

_ACCEPTED_RETENTION_MIN_DAYS = 30
_ACCEPTED_RETENTION_MAX_DAYS = 2555
_QUARANTINE_RETENTION_MIN_DAYS = 7
_QUARANTINE_RETENTION_MAX_DAYS = 365

# HTTP request bodies are already bounded well below 65536 bytes by the
# payload_limits policy; this is a *separate* storage-envelope bound (Slice
# 8.3) that accounts for the additional acceptance/identity/source-contract
# wrapper material added around the projected payload. It is deliberately
# generous relative to the HTTP transport limit, not equal to it.
_MIN_ENVELOPE_BYTES = 1024
_MAX_ENVELOPE_BYTES = 131_072
_DEFAULT_MAX_ENVELOPE_BYTES = 70_000

_ALL_EVENT_STREAMS: tuple[str, ...] = tuple(sorted(item.value for item in EventStream))


@dataclass(frozen=True, slots=True)
class CommunityDataLakePolicy:
    """Deterministic, review-required policy for the Community Data Lake."""

    policy_id: str = COMMUNITY_DATA_LAKE_POLICY_ID
    policy_version: str = COMMUNITY_DATA_LAKE_POLICY_VERSION
    envelope_schema_version: str = COMMUNITY_DATA_LAKE_ENVELOPE_SCHEMA_VERSION
    accepted_retention_days: int = 365
    quarantine_retention_days: int = 90
    incomplete_multipart_days: int = 7
    noncurrent_version_expiration_days: int = 30
    encryption_mode: EncryptionMode = EncryptionMode.SSE_S3
    enable_versioning: bool = True
    bucket_strategy: str = "single_bucket_prefix_isolation"
    accepted_prefix: str = "raw/"
    quarantine_prefix: str = "quarantine/"
    hive_style_partitions: bool = True
    allowed_event_streams: tuple[str, ...] = _ALL_EVENT_STREAMS
    # Storage envelope size bound (Slice 8.3) — distinct from the HTTP
    # request-body transport limit. Default of 70_000 bytes covers the
    # standard 65_536-byte HTTP limit plus nested acceptance/identity/
    # source-contract envelope overhead.
    max_envelope_bytes: int = _DEFAULT_MAX_ENVELOPE_BYTES
    limitations: tuple[str, ...] = (
        "defaults_require_product_policy_review",
        "in_memory_store_reference_implementation_only",
        "no_boto3_dependency",
        "no_endpoint_or_app_wiring",
        "opentofu_bucket_foundation_unwired_from_ingestion",
    )

    def __post_init__(self) -> None:
        self.validate()
        object.__setattr__(
            self,
            "allowed_event_streams",
            tuple(sorted(set(self.allowed_event_streams))),
        )
        object.__setattr__(self, "limitations", tuple(sorted(set(self.limitations))))

    @property
    def policy_token(self) -> str:
        return f"{self.policy_id}:{self.policy_version}"

    def validate(self) -> None:
        if self.policy_id != COMMUNITY_DATA_LAKE_POLICY_ID:
            raise ValueError("unsupported data lake policy id")
        if self.policy_version != COMMUNITY_DATA_LAKE_POLICY_VERSION:
            raise ValueError("unsupported data lake policy version")
        if self.envelope_schema_version != COMMUNITY_DATA_LAKE_ENVELOPE_SCHEMA_VERSION:
            raise ValueError("unsupported data lake envelope schema version")
        if not (
            _ACCEPTED_RETENTION_MIN_DAYS
            <= self.accepted_retention_days
            <= _ACCEPTED_RETENTION_MAX_DAYS
        ):
            raise ValueError(
                "accepted_retention_days out of bounds "
                f"[{_ACCEPTED_RETENTION_MIN_DAYS}, {_ACCEPTED_RETENTION_MAX_DAYS}]"
            )
        if not (
            _QUARANTINE_RETENTION_MIN_DAYS
            <= self.quarantine_retention_days
            <= _QUARANTINE_RETENTION_MAX_DAYS
        ):
            raise ValueError(
                "quarantine_retention_days out of bounds "
                f"[{_QUARANTINE_RETENTION_MIN_DAYS}, {_QUARANTINE_RETENTION_MAX_DAYS}]"
            )
        # Slice 8.10: quarantine must not outlive accepted raw by default.
        if self.quarantine_retention_days > self.accepted_retention_days:
            raise ValueError(
                "quarantine_retention_days must be less than or equal to "
                "accepted_retention_days"
            )
        if self.incomplete_multipart_days <= 0:
            raise ValueError("incomplete_multipart_days must be positive")
        if self.noncurrent_version_expiration_days <= 0:
            raise ValueError("noncurrent_version_expiration_days must be positive")
        if self.encryption_mode != EncryptionMode.SSE_S3:
            raise ValueError(
                "encryption_mode must be sse_s3 in v0.2.0; sse_kms is a future migration"
            )
        if not self.accepted_prefix.endswith("/"):
            raise ValueError("accepted_prefix must end with '/'")
        if not self.quarantine_prefix.endswith("/"):
            raise ValueError("quarantine_prefix must end with '/'")
        if self.accepted_prefix == self.quarantine_prefix:
            raise ValueError("accepted_prefix and quarantine_prefix must differ")
        if not self.allowed_event_streams:
            raise ValueError("allowed_event_streams must not be empty")
        valid_streams = {item.value for item in EventStream}
        for stream in self.allowed_event_streams:
            if stream not in valid_streams:
                raise ValueError(f"invalid allowed event stream: {stream}")
        if not (_MIN_ENVELOPE_BYTES <= self.max_envelope_bytes <= _MAX_ENVELOPE_BYTES):
            raise ValueError(
                f"max_envelope_bytes out of bounds [{_MIN_ENVELOPE_BYTES}, {_MAX_ENVELOPE_BYTES}]"
            )

    @classmethod
    def default(cls) -> CommunityDataLakePolicy:
        return cls()

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "accepted_prefix": self.accepted_prefix,
            "accepted_retention_days": self.accepted_retention_days,
            "allowed_event_streams": list(self.allowed_event_streams),
            "bucket_strategy": self.bucket_strategy,
            "enable_versioning": self.enable_versioning,
            "encryption_mode": self.encryption_mode.value,
            "envelope_schema_version": self.envelope_schema_version,
            "hive_style_partitions": self.hive_style_partitions,
            "incomplete_multipart_days": self.incomplete_multipart_days,
            "limitations": list(self.limitations),
            "max_envelope_bytes": self.max_envelope_bytes,
            "noncurrent_version_expiration_days": self.noncurrent_version_expiration_days,
            "policy_id": self.policy_id,
            "policy_token": self.policy_token,
            "policy_version": self.policy_version,
            "quarantine_prefix": self.quarantine_prefix,
            "quarantine_retention_days": self.quarantine_retention_days,
        }


def default_data_lake_policy() -> CommunityDataLakePolicy:
    return CommunityDataLakePolicy.default()
