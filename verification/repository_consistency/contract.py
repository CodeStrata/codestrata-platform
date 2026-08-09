"""Contract for Slice 16.8 repository consistency validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.repository_consistency import (
    REPOSITORY_CONSISTENCY_ID,
    REPOSITORY_CONSISTENCY_VERSION,
)

SCHEMA_NAME = "repository-consistency-verification"
SCHEMA_VERSION = "1.0.0"
SV168_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv16-8"
REPORT_JSON = "repository-consistency-verification.json"
REPORT_MD = "repository-consistency-verification.md"

POLICY_RELATIVE = "platform/policies/repository_consistency_policy.json"
POLICY_SCHEMA = "repository-consistency-policy:1.0"
OWNER_REGISTER_RELATIVE = "platform/policies/repository_owner_review_register.json"
OWNER_REGISTER_SCHEMA = "repository-owner-review-register:1.0"

REQUIRED_TOP_LEVEL = (
    "engine",
    "platform",
    "infrastructure",
    "vscode-plugin",
    "insights",
    "docs",
    "design-system",
    "verification",
    "tests",
    "scripts",
    "governance",
    "validation",
    "examples",
)

FORBIDDEN_TOP_LEVEL = ("cursor-plugin", "codestrata-cursor")

EXPORT_TARGETS = ("community", "infrastructure", "insights")
FORBIDDEN_EXPORT_TARGETS = ("platform", "cursor", "codestrata-cursor")

VERSION_ANCHORS = {
    "engine_cli": "0.2.0",
    "vscode": "0.2.0",
    "assessment": "1.2",
}

PRIOR_SV16 = tuple(f"sv16-{i}" for i in range(1, 9))


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv168Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = REPOSITORY_CONSISTENCY_ID
    package_version: str = REPOSITORY_CONSISTENCY_VERSION
    start_slice_16_8: bool = True
    start_slice_16_9: bool = True
    start_slice_16_10: bool = True
    start_epic_17: bool = True
    start_slice_17_2: bool = True
    no_remote_creation: bool = True
    no_cutover: bool = True
    production_ingestion_enabled: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True


def default_contract() -> Sv168Contract:
    return Sv168Contract()
