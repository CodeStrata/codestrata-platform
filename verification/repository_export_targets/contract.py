"""Contract constants for Slice 12.8."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.repository_export_targets import (
    REPOSITORY_EXPORT_TARGETS_ID,
    REPOSITORY_EXPORT_TARGETS_VERSION,
)

SCHEMA_NAME = "repository-export-target-verification"
SCHEMA_VERSION = "1.0.0"

SV128_OUTPUT_RELATIVE = "reports/verification/sv12-8"
REPORT_JSON = "repository-export-target-verification.json"

AUTHORITATIVE_COMMAND = "scripts/export_repository.py"
SUPPORTED_TARGETS = ("community", "infrastructure", "insights")
TARGET_VISIBILITY = {
    "community": "public_product_export",
    "infrastructure": "private",
    "insights": "private_internal_application",
}
TARGET_MANIFEST_SCHEMAS = {
    "community": "codestrata.community_release:2",
    "infrastructure": "infrastructure-repository-export-manifest:1.0.0",
    "insights": "insights-repository-export-manifest:1.0.0",
}

ASSESSMENT_SCHEMA_VERSION = "1.2"


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv128Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = REPOSITORY_EXPORT_TARGETS_ID
    package_version: str = REPOSITORY_EXPORT_TARGETS_VERSION
    start_slice_12_9: bool = False
    no_git: bool = True
    no_aws: bool = True
    no_opentofu_exec: bool = True
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True
    assessment_schema_version: str = ASSESSMENT_SCHEMA_VERSION


def default_contract() -> Sv128Contract:
    return Sv128Contract()
