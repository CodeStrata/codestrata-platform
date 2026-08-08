"""Contract for Slice 16.7 repository boundary & residency."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.repository_boundary_residency import (
    REPOSITORY_BOUNDARY_RESIDENCY_ID,
    REPOSITORY_BOUNDARY_RESIDENCY_VERSION,
)

SCHEMA_NAME = "repository-boundary-residency-verification"
SCHEMA_VERSION = "1.0.0"
SV167_OUTPUT_RELATIVE = "reports/verification/sv16-7"
REPORT_JSON = "repository-boundary-residency-verification.json"
REPORT_MD = "repository-boundary-residency-verification.md"

POLICY_RELATIVE = "platform/policies/repository_boundary_residency_policy.json"
POLICY_SCHEMA = "repository-boundary-residency-policy:1.0"
RESIDENCY_MAP_RELATIVE = "platform/policies/repository_residency_map.json"
PLATFORM_REGISTER_RELATIVE = "platform/policies/platform_package_register.json"

CLASSIFICATIONS: tuple[str, ...] = (
    "CORRECT_RESIDENCY",
    "MOVE_WITHIN_MONOREPO",
    "EXPORT_TO_FUTURE_REPOSITORY",
    "GENERATE_FOR_CONSUMER",
    "SHARED_AUTHORITY",
    "COMPATIBILITY_RETAIN",
    "HISTORICAL_RETAIN",
    "OWNER_REVIEW_REQUIRED",
    "REMOVE_IF_DUPLICATE",
    "DEFER_UNTIL_CUTOVER",
)

PLATFORM_PACKAGE_CLASSES: tuple[str, ...] = (
    "ACTIVE_COMMUNITY_BACKEND",
    "ACTIVE_INTERNAL_INSIGHTS_BACKEND",
    "COMMERCIAL_PROTOTYPE",
    "SHARED_INFRA_HELPER",
    "OWNER_REVIEW_REQUIRED",
    "MOVE_CANDIDATE",
    "REMOVE_CANDIDATE",
)

REQUIRED_COMPONENTS: tuple[str, ...] = (
    "engine",
    "platform",
    "infrastructure",
    "insights",
    "docs",
    "vscode",
    "design-system",
    "verification",
    "brand-master",
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv167Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = REPOSITORY_BOUNDARY_RESIDENCY_ID
    package_version: str = REPOSITORY_BOUNDARY_RESIDENCY_VERSION
    start_slice_16_8: bool = True
    start_slice_16_9: bool = True
    start_slice_16_10: bool = True
    start_epic_17: bool = False
    no_remote_creation: bool = True
    no_cutover: bool = True
    no_dual_authoring: bool = True
    production_ingestion_enabled: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True


def default_contract() -> Sv167Contract:
    return Sv167Contract()
