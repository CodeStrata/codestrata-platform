"""Contract constants for SV.16 release artifact verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.release_artifacts import (
    RELEASE_ARTIFACTS_ID,
    RELEASE_ARTIFACTS_VERSION,
)

INTENDED_RELEASE_VERSION = "0.2.0"
SCHEMA_NAME = "release-artifact-verification"
SCHEMA_VERSION = "1.0.0"
TARGET_REPOSITORY_COUNT = 22

SV16_OUTPUT_RELATIVE = "reports/verification/sv16"
ARTIFACTS_SUBDIR = "artifacts"

REPORT_JSON = "release-artifact-verification.json"
REPORT_MD = "release-artifact-verification.md"
RELEASE_NOTES_INPUT_JSON = "release-notes-input.json"

# Authoritative EI identities (post-SV.13).
AUTHORITATIVE_DATASET_ID = "dataset:3da1c591fcef727714304861"
AUTHORITATIVE_AGGREGATION_ID = "aggregation:016d8960799e133ee200c252"
AUTHORITATIVE_EIR_ID = "eir:1eda169bfe4b7041265b253e"
AUTHORITATIVE_INTERP_BUNDLE = "interp-bundle:c719915c68cf94601a0e8f0b"
AUTHORITATIVE_EXPORT_ID = "eir-export:ca01b398f777e20ef75ea1f2"
AUTHORITATIVE_REPOSITORY_COUNT = 22

SV10_OUTPUT_RELATIVE = "engine/reports/verification/sv10"
SV11_REPORT_RELATIVE = (
    "engine/reports/verification/sv11/assessment-consistency-verification.json"
)
SV12_OUTPUT_RELATIVE = "platform/reports/verification/sv12"
SV13_OUTPUT_RELATIVE = "platform/reports/verification/sv13"
SV14_OUTPUT_RELATIVE = "platform/reports/verification/sv14"
SV15_OUTPUT_RELATIVE = "platform/reports/verification/sv15"

DEMO_RELATIVE = "platform/demo"
SV12_EXPORT_MANIFEST = f"{SV12_OUTPUT_RELATIVE}/export-manifest.json"

DATASET_DISCLAIMER = (
    "Results describe only the 22 curated pinned repositories in the v0.2.0 "
    "release-validation catalog and are not a product-wide accuracy or "
    "industry benchmark claim."
)

OPENTOFU_WAIVER = False


def monorepo_root_from_here() -> Path:
    """Resolve monorepo root from ``verification/release_artifacts/*.py``."""

    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv16Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = RELEASE_ARTIFACTS_ID
    package_version: str = RELEASE_ARTIFACTS_VERSION
    intended_release_version: str = INTENDED_RELEASE_VERSION
    target_repository_count: int = TARGET_REPOSITORY_COUNT
    start_sv17: bool = False
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True
    no_tofu_apply: bool = True
    opentofu_waiver: bool = OPENTOFU_WAIVER


def default_contract() -> Sv16Contract:
    return Sv16Contract()
