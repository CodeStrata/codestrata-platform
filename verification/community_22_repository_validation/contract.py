"""Contract for Slice 17.13."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_22_repository_validation import (
    COMMUNITY_22_REPOSITORY_VALIDATION_ID,
    VERSION,
)

SCHEMA_NAME = "community-22-repository-validation-verification"
SCHEMA_VERSION = "1.0.0"
SUITE_ID = "sv17-13"
SV1713_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-13"
REPORT_JSON = "community-22-repository-validation-verification.json"
REPORT_MD = "community-22-repository-validation-verification.md"
MANIFEST_JSON = "manifest.json"

POLICY_RELATIVE = "platform/policies/community_22_repository_validation_policy.json"
POLICY_SCHEMA = "community-22-repository-validation-policy:1.0"
SUITE_REGISTER_RELATIVE = "platform/policies/community_validation_suite_register.json"
SUITE_REGISTER_SCHEMA = "community-validation-suite-register:1.0"
RESULT_REGISTER_RELATIVE = "platform/policies/community_validation_repository_result_register.json"
RESULT_REGISTER_SCHEMA = "community-validation-repository-result-register:1.0"
CONTRACT_RELATIVE = "platform/contracts/community_22_repository_validation_verification.json"

CATALOG_RELATIVE = "validation/repository-catalog/catalog.json"

ARTIFACT_ROOT = ".codestrata-artifacts"
ASSESSMENTS_RELATIVE = ".codestrata-artifacts/assessments"
INTELLIGENCE_RELATIVE = ".codestrata-artifacts/intelligence"
VALIDATION_RELATIVE = ".codestrata-artifacts/validation"
VALIDATION_REPOSITORIES_RELATIVE = ".codestrata-artifacts/validation/repositories"
VALIDATION_LOGS_RELATIVE = ".codestrata-artifacts/validation/logs"
VALIDATION_SUITES_RELATIVE = ".codestrata-artifacts/validation/suites"

ENGINE_HEADS_MODULE = "engine/src/codestrata/artifacts/heads.py"

REPOSITORY_TARGET = 22
PORTFOLIO_EIR_COUNT = 1

SOFT_LIMITATION_CODES = frozenset(
    {
        "full_22_repository_suite_not_executed",
        "assessment_pass_not_invented_pre_execution",
        "scaffolding_offline_checks_only",
        "portfolio_eir_build_not_executed",
        "synthetic_validation_installation_identity",
        "telemetry_transport_unavailable_or_no_suite_delta",
        "owner_rotation_required_global_git_insteadof",
        "monorepo_pre_cutover_source_authority",
        "worktree_uncommitted",
        "insights_soft_limitations_present",
        "doris_limited_head_coverage",
        "performance_acceptable_v0_2_0",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1713Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_22_REPOSITORY_VALIDATION_ID
    package_version: str = VERSION
    suite_id: str = SUITE_ID
    repository_target: int = REPOSITORY_TARGET
    start_slice_17_13: bool = True
    start_slice_17_14: bool = False


def default_contract() -> Sv1713Contract:
    return Sv1713Contract()
