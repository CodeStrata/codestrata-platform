"""Contract for Slice 17.15 report artifact lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCHEMA_NAME = "report-artifact-lifecycle-verification"
SCHEMA_VERSION = "1.0.0"
SUITE_ID = "sv17-15"
SV1715_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-15"
REPORT_JSON = "report-artifact-lifecycle-verification.json"
REPORT_MD = "report-artifact-lifecycle-verification.md"

POLICY_RELATIVE = "platform/policies/codestrata_report_retention_policy.json"
POLICY_SCHEMA = "codestrata-report-retention-policy:1.0"
REGISTER_RELATIVE = "platform/policies/codestrata_report_lifecycle_register.json"
REGISTER_SCHEMA = "codestrata-report-lifecycle-register:1.0"
CONTRACT_RELATIVE = "platform/contracts/report_artifact_lifecycle_verification.json"

ARTIFACT_ROOT = ".codestrata-artifacts"
ASSESSMENTS_LAYOUT = f"{ARTIFACT_ROOT}/assessments/<repository-id>/{{current,previous}}/"
INTELLIGENCE_LAYOUT = f"{ARTIFACT_ROOT}/intelligence/<portfolio-id>/{{current,previous}}/"

ENGINE_REPOSITORY_IDENTITY = "engine/src/codestrata/artifacts/repository_identity.py"
ENGINE_PORTFOLIO_IDENTITY = "engine/src/codestrata/artifacts/portfolio_identity.py"
ENGINE_LIFECYCLE = "engine/src/codestrata/artifacts/lifecycle.py"
ENGINE_LAYOUT = "engine/src/codestrata/artifacts/layout.py"
ENGINE_REPORT_PATHS = "engine/src/codestrata/reporters/report_paths.py"
ENGINE_MANIFEST = "engine/src/codestrata/artifacts/manifest.py"

REPOSITORY_ID_FORMATS = ("github-<owner>-<repo>", "local-<safe-name>")
SLOTS = ("current", "previous")
MAX_VERSIONS = 2

PRIOR_POLICY_PATHS = (
    "platform/policies/community_api_domain_policy.json",
    "platform/policies/community_22_repository_validation_policy.json",
)

PRIOR_VERIFICATION_PACKAGES = (
    "verification/community_api_domain",
    "verification/community_22_repository_validation",
)

SOFT_LIMITATION_CODES = frozenset(
    {
        "legacy_run_id_folder_aliases",
        "previous_ui_deferred",
        "cloud_deferred",
        "monorepo_pre_cutover",
        "worktree_uncommitted",
        "engine_lifecycle_not_wired",
    }
)

POLICY_REQUIRED_VALUES: dict[str, object] = {
    "repository_folder_identity": "human_readable_logical_repository",
    "portfolio_folder_identity": "human_readable_logical_portfolio",
    "run_ids_are_metadata": True,
    "assessment_versions_per_repository": 2,
    "engineering_intelligence_versions_per_portfolio": 2,
    "slots": ["current", "previous"],
    "failed_assessment_promotes": False,
    "failed_eir_promotes": False,
    "rotation_atomic": True,
    "portfolio_membership_change_preserves_identity": True,
    "telemetry_data_lake_uses_report_retention": False,
    "validation_artifacts_use_report_retention": False,
    "future_cloud_reports_same_retention": True,
    "start_slice_17_15": True,
    "start_slice_17_16": True,
    "start_slice_17_17": False,
}


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1715Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    start_slice_17_15: bool = True
    start_slice_17_16: bool = True
    artifact_root: str = ARTIFACT_ROOT


def default_contract() -> Sv1715Contract:
    return Sv1715Contract()
