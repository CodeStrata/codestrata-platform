"""Contract for Community Data Lake integration verification (Slice 8.14 / SV.9).

Verification schema only — not a product schema. Does not bump Data Lake
policy, envelope, quarantine, retention, encryption, access, or storage
policy versions.
"""

from __future__ import annotations

from dataclasses import dataclass

COMMUNITY_DATA_LAKE_VERIFICATION_ID = "community-data-lake-verification"
COMMUNITY_DATA_LAKE_VERIFICATION_VERSION = "1.0.0"

ACCEPTED_STREAMS: tuple[str, ...] = (
    "telemetry",
    "assessment_metadata",
    "cli_event",
    "extension_event",
    "ai_usage",
)

FIXED_ACCEPTANCE_UTC = "2026-08-04T12:00:00+00:00"

FORBIDDEN_REPORT_FRAGMENTS: tuple[str, ...] = (
    "Authorization:",
    "Bearer cscc_v1_",
    "/Users/",
    "/home/",
    "file://",
    "arn:aws:",
    "AKIA",
    "aws_secret_access_key",
    "codestrata-test-lake-bucket",  # even test bucket names stay out of reports
)

DEFAULT_LIMITATIONS: tuple[str, ...] = (
    "no_real_aws_integration",
    "production_wiring_deliberately_disabled",
    "no_atomic_identity_storage_coordination",
    "no_exactly_once_claim",
    "lifecycle_time_not_simulated",
)


@dataclass(frozen=True, slots=True)
class DataLakeVerificationContract:
    verification_id: str = COMMUNITY_DATA_LAKE_VERIFICATION_ID
    schema_version: str = COMMUNITY_DATA_LAKE_VERIFICATION_VERSION
    notes: tuple[str, ...] = (
        "SV.9 verifies Community Data Lake foundation contracts end-to-end.",
        "Uses in-memory and strict fake-S3 adapters only; no real AWS.",
        "Does not enable production ingestion or attach writer IAM.",
        "Does not start Epic 9.",
    )


def default_contract() -> DataLakeVerificationContract:
    return DataLakeVerificationContract()


__all__ = [
    "ACCEPTED_STREAMS",
    "COMMUNITY_DATA_LAKE_VERIFICATION_ID",
    "COMMUNITY_DATA_LAKE_VERIFICATION_VERSION",
    "DEFAULT_LIMITATIONS",
    "DataLakeVerificationContract",
    "FIXED_ACCEPTANCE_UTC",
    "FORBIDDEN_REPORT_FRAGMENTS",
    "default_contract",
]
