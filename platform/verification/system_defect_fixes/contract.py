"""Contract constants for SV.13 unsafe-metadata defect fix."""

from __future__ import annotations

from dataclasses import dataclass

from verification.system_defect_fixes import (
    SYSTEM_DEFECT_FIXES_ID,
    SYSTEM_DEFECT_FIXES_VERSION,
)

SCHEMA_NAME = "system-defect-fixes-verification"
SCHEMA_VERSION = "1.0.0"
DEFECT_ID = "SV.13-EI-UNSAFE-METADATA"
TARGET_REPOSITORY_COUNT = 22
ASSESSMENT_SCHEMA_VERSION = "1.2"
EIR_SCHEMA_VERSION = "1.0"
WEBSITE_EXPORT_SCHEMA_VERSION = "1.0"

# Repositories rejected by SV.12 Platform EI ingestion (unsafe_metadata).
AFFECTED_REPOSITORY_IDS: tuple[str, ...] = (
    "dubbo",
    "juice-shop",
    "nodegoat",
)

# Finding rule for all three rejections (SEC002 private-key header evidence).
AFFECTED_RULE_ID = "SEC002"

SV10_OUTPUT_RELATIVE = "engine/reports/verification/sv10"
SV11_OUTPUT_RELATIVE = "engine/reports/verification/sv11"
SV12_OUTPUT_RELATIVE = "platform/reports/verification/sv12"
SV13_OUTPUT_RELATIVE = "platform/reports/verification/sv13"

LEDGER_JSON = "sv13-defect-ledger.json"
VERIFICATION_JSON = "system-defect-fixes-verification.json"
VERIFICATION_MD = "system-defect-fixes-verification.md"

DATASET_DISCLAIMER = (
    "Results describe only the 22 curated pinned repositories in the v0.2.0 "
    "release-validation catalog and are not a product-wide accuracy or "
    "industry benchmark claim."
)


@dataclass(frozen=True, slots=True)
class Sv13Contract:
    defect_id: str = DEFECT_ID
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = SYSTEM_DEFECT_FIXES_ID
    package_version: str = SYSTEM_DEFECT_FIXES_VERSION
    target_repository_count: int = TARGET_REPOSITORY_COUNT
    start_sv14: bool = False
    weaken_privacy: bool = False
    repository_specific_allowlist: bool = False
    known_issues_bypass: bool = False


def default_contract() -> Sv13Contract:
    return Sv13Contract()
