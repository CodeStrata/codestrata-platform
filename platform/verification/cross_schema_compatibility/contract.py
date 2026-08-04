"""Contract constants for SV.14 cross-schema compatibility verification."""

from __future__ import annotations

from dataclasses import dataclass

from verification.cross_schema_compatibility import (
    CROSS_SCHEMA_COMPATIBILITY_ID,
    CROSS_SCHEMA_COMPATIBILITY_VERSION,
)

SCHEMA_NAME = "cross-schema-compatibility-verification"
SCHEMA_VERSION = "1.0.0"
TARGET_REPOSITORY_COUNT = 22

# Product schema versions (referenced, not redefined as authority).
ASSESSMENT_SCHEMA_VERSION = "1.2"
VALIDATION_RECORD_SCHEMA_VERSION = "1.0"
VALIDATION_SUMMARY_SCHEMA_VERSION = "1.0"
EIR_SCHEMA_VERSION = "1.0"
WEBSITE_EXPORT_SCHEMA_VERSION = "1.0"
COMMUNITY_CLOUD_API_SCHEMA_VERSION = "1.0"
VERIFICATION_REPORT_SCHEMA_VERSION = "1.0.0"

SV10_OUTPUT_RELATIVE = "engine/reports/verification/sv10"
SV11_REPORT_RELATIVE = (
    "engine/reports/verification/sv11/assessment-consistency-verification.json"
)
SV12_OUTPUT_RELATIVE = "platform/reports/verification/sv12"
SV13_LEDGER_RELATIVE = (
    "platform/reports/verification/sv13/sv13-defect-ledger.json"
)
SV14_OUTPUT_RELATIVE = "platform/reports/verification/sv14"

REPORT_JSON = "cross-schema-compatibility-verification.json"
REPORT_MD = "cross-schema-compatibility-verification.md"

EIR_JSON = "engineering-intelligence-report.json"
EXPORT_MANIFEST = "export-manifest.json"
WEBSITE_JSON = "engineering-intelligence-report.json"
WEBSITE_HTML = "engineering-intelligence-report.html"

CATALOG_RELATIVE = "validation/repository-catalog/catalog.json"
VALIDATION_SUMMARY_RELATIVE = (
    "engine/validation/results/summaries/latest/validation-summary.json"
)

DATASET_DISCLAIMER = (
    "Results describe only the 22 curated pinned repositories in the v0.2.0 "
    "release-validation catalog and are not a product-wide accuracy or "
    "industry benchmark claim. Product schema 1.0 and verification schema "
    "1.0.0 are distinct versioning namespaces."
)


@dataclass(frozen=True, slots=True)
class Sv14Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = CROSS_SCHEMA_COMPATIBILITY_ID
    package_version: str = CROSS_SCHEMA_COMPATIBILITY_VERSION
    target_repository_count: int = TARGET_REPOSITORY_COUNT
    start_sv15: bool = False
    redesign_schemas: bool = False
    speculative_aliases: bool = False
    migrate_stored_artifacts: bool = False


def default_contract() -> Sv14Contract:
    return Sv14Contract()
