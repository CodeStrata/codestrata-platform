"""Contract for Community Data Lake completion verification (Slice 8.15).

Verification schema only — not a product schema. Confirms Epic 8 boundary and
completion without enabling production ingestion or starting Epic 9.
"""

from __future__ import annotations

from dataclasses import dataclass

from verification.community_data_lake.contract import ACCEPTED_STREAMS

COMMUNITY_DATA_LAKE_COMPLETION_ID = "community-data-lake-completion-verification"
COMMUNITY_DATA_LAKE_COMPLETION_VERSION = "1.0.0"

EPIC = "8"
SLICES_COMPLETED: tuple[str, ...] = tuple(f"8.{i}" for i in range(1, 16))

INTEGRATION_REPORT_FILENAME = "community-data-lake-verification.json"

FORBIDDEN_REPORT_FRAGMENTS: tuple[str, ...] = (
    "Authorization:",
    "Bearer cscc_v1_",
    "/Users/",
    "/home/",
    "file://",
    "arn:aws:",
    "AKIA",
    "aws_secret_access_key",
    "codestrata-test-lake-bucket",
)

DEFAULT_LIMITATIONS: tuple[str, ...] = (
    "no_real_aws",
    "production_wiring_disabled",
    "no_atomic_identity_storage_tx",
    "no_analytics",
    "provisional_retention",
    "kms_deferred",
    "no_deny_unencrypted_writes",
    "no_exactly_once_claim",
    "no_durable_ingestion_operational",
    "epic_9_not_started",
)

INTENTIONALLY_EXCLUDED: tuple[str, ...] = (
    "production_ingestion_wiring",
    "writer_iam_attachment",
    "endpoint_to_s3_connection",
    "analytics_pipeline",
    "epic_9",
)


@dataclass(frozen=True, slots=True)
class CompletionVerificationContract:
    schema_name: str = COMMUNITY_DATA_LAKE_COMPLETION_ID
    schema_version: str = COMMUNITY_DATA_LAKE_COMPLETION_VERSION
    epic: str = EPIC
    slices_completed: tuple[str, ...] = SLICES_COMPLETED
    notes: tuple[str, ...] = (
        "Slice 8.15 verifies Epic 8 boundary and completion only.",
        "Reuses SV.9 integration verification report; does not duplicate its suite.",
        "Production ingestion remains deliberately disabled.",
        "Does not start Epic 9.",
    )


def default_contract() -> CompletionVerificationContract:
    return CompletionVerificationContract()


__all__ = [
    "ACCEPTED_STREAMS",
    "COMMUNITY_DATA_LAKE_COMPLETION_ID",
    "COMMUNITY_DATA_LAKE_COMPLETION_VERSION",
    "DEFAULT_LIMITATIONS",
    "EPIC",
    "FORBIDDEN_REPORT_FRAGMENTS",
    "INTEGRATION_REPORT_FILENAME",
    "INTENTIONALLY_EXCLUDED",
    "SLICES_COMPLETED",
    "CompletionVerificationContract",
    "default_contract",
]
