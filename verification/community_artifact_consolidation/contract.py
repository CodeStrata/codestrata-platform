"""Contract for Slice 17.12."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_artifact_consolidation import (
    COMMUNITY_ARTIFACT_CONSOLIDATION_ID,
    VERSION,
)

SCHEMA_NAME = "community-artifact-consolidation-verification"
SCHEMA_VERSION = "1.0.0"
SV1712_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-12"
REPORT_JSON = "community-artifact-consolidation-verification.json"
REPORT_MD = "community-artifact-consolidation-verification.md"

POLICY_RELATIVE = "platform/policies/community_artifact_consolidation_policy.json"
POLICY_SCHEMA = "community-artifact-consolidation-policy:1.0"
REGISTER_RELATIVE = "platform/policies/community_artifact_consolidation_register.json"
REGISTER_SCHEMA = "community-artifact-consolidation-register:1.0"
CONTRACT_RELATIVE = "platform/contracts/community_artifact_consolidation_verification.json"

ARTIFACT_ROOT = ".codestrata-artifacts"
ASSESSMENTS_RELATIVE = ".codestrata-artifacts/assessments"
INTELLIGENCE_RELATIVE = ".codestrata-artifacts/intelligence"
VALIDATION_RELATIVE = ".codestrata-artifacts/validation"
MANIFESTS_RELATIVE = ".codestrata-artifacts/manifests"
TEMPORARY_RELATIVE = ".codestrata-artifacts/temporary"

ENGINE_ARTIFACTS_PACKAGE = "engine/src/codestrata/artifacts"
REPORT_PATHS = "engine/src/codestrata/reporters/report_paths.py"
MODERNIZATION_SERIALIZATION = "engine/src/codestrata/reporting/modernization_serialization.py"
VSCODE_SETTINGS = "vscode-plugin/src/config/settings.ts"
VSCODE_POLICY = "vscode-plugin/src/reportOpening/policy.ts"
CLI_REPORT = "engine/src/codestrata/cli/report.py"
GITIGNORE = ".gitignore"
SCAN_BOUNDARY = "engine/src/codestrata/scan_boundary/policy.py"

SOFT_LIMITATION_CODES = frozenset(
    {
        "monorepo_remains_source_authority_pre_cutover",
        "worktree_uncommitted",
        "legacy_reports_may_still_exist_until_migrated",
        "engineering_intelligence_filenames_retain_report_suffix",
        "full_historical_verification_suite_path_rewrite_soft",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1712Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_ARTIFACT_CONSOLIDATION_ID
    package_version: str = VERSION
    start_slice_17_12: bool = True
    start_slice_17_13: bool = False


def default_contract() -> Sv1712Contract:
    return Sv1712Contract()
