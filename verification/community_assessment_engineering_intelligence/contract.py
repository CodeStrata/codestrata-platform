"""Contract for Slice 17.19."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCHEMA_NAME = "community-assessment-engineering-intelligence-verification"
SCHEMA_VERSION = "1.0.0"
SUITE_ID = "sv17-19"
SV1719_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-19"
REPORT_JSON = "community-assessment-engineering-intelligence-verification.json"
REPORT_MD = "community-assessment-engineering-intelligence-verification.md"

POLICY_RELATIVE = (
    "platform/policies/community_assessment_engineering_intelligence_validation_policy.json"
)
POLICY_SCHEMA = "community-assessment-engineering-intelligence-validation-policy:1.0"
ASSESSMENT_REGISTER = "platform/policies/community_assessment_report_register.json"
EIR_REGISTER = "platform/policies/community_engineering_intelligence_report_register.json"
CONTRACT_RELATIVE = (
    "platform/contracts/community_assessment_engineering_intelligence_verification.json"
)

HEADS_PY = "engine/src/codestrata/artifacts/heads.py"
MANIFEST_PY = "engine/src/codestrata/artifacts/manifest.py"
LIFECYCLE_PY = "engine/src/codestrata/artifacts/lifecycle.py"
CATALOG_RELATIVE = "validation/repository-catalog/catalog.json"
ASSESSMENTS_RELATIVE = ".codestrata-artifacts/assessments"
INTELLIGENCE_RELATIVE = ".codestrata-artifacts/intelligence"
PORTFOLIO_ID = "sv17-19-validation"

POLICY_REQUIRED_VALUES: dict[str, object] = {
    "assessment_repository_level": True,
    "assessment_heads_source_of_truth": True,
    "assessment_manifest_lightweight": True,
    "eir_portfolio_level": True,
    "eir_requires_multiple_repository_assessments": True,
    "assessment_evidence_traceable": True,
    "eir_conclusions_traceable": True,
    "current_previous_lifecycle": True,
    "failed_generation_does_not_promote": True,
    "reports_excluded_from_data_lake": True,
    "full_22_repo_release_corpus": False,
    "representative_subset_required": True,
    "ai_not_required_for_basic_assessment": True,
    "community_status_website_deferred": True,
    "start_slice_17_19": True,
    "start_slice_17_20": True,
}

EXPECTED_17_19_PACKAGE = "verification/community_assessment_engineering_intelligence"
EXPECTED_17_20_PACKAGE = "verification/community_ai_providers"
SLICE_17_21_PACKAGE_CANDIDATES = (
    "verification/community_production_slice_17_21",
    "verification/community_vscode_publish",
    "verification/community_status_api",
    "verification/community_website_status",
)

SOFT_LIMITATION_CODES = frozenset(
    {
        "bounded_representative_subset",
        "individual_head_insufficient_evidence",
        "unsupported_head_for_technology",
        "ai_narrative_not_requested",
        "low_portfolio_size",
        "worktree_uncommitted",
        "monorepo_pre_cutover_source_authority",
        "controlled_lifecycle_source_proven",
    }
)

REPRESENTATIVE_CATALOG_IDS = (
    "flask",
    "express",
    "juice-shop",
    "spring-petclinic",
    "vite",
    "nodegoat",
)

ASSESSMENT_MANIFEST_SCHEMA = "codestrata-assessment-manifest:1.0.0"
EIR_JSON = "engineering-intelligence-report.json"
EIR_HTML = "engineering-intelligence-report.html"
ASSESSMENT_JSON = "assessment.json"
ASSESSMENT_HTML = "assessment.html"


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1719Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    start_slice_17_19: bool = True
    start_slice_17_20: bool = True


def default_contract() -> Sv1719Contract:
    return Sv1719Contract()
