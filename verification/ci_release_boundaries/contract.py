"""Contract constants for Slice 12.9."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.ci_release_boundaries import (
    CI_RELEASE_BOUNDARIES_ID,
    CI_RELEASE_BOUNDARIES_VERSION,
)

SCHEMA_NAME = "ci-release-boundary-verification"
SCHEMA_VERSION = "1.0.0"

SV129_OUTPUT_RELATIVE = "reports/verification/sv12-9"
REPORT_JSON = "ci-release-boundary-verification.json"
REPORT_MD = "ci-release-boundary-verification.md"

AUTHORITATIVE_EXPORT_COMMAND = "scripts/export_repository.py"
SUPPORTED_EXPORT_TARGETS = ("community", "infrastructure", "insights")
ACTIVE_EDITOR_EXTENSIONS = ("vscode",)

REQUIRED_CI_JOBS = (
    "engine-tests",
    "platform-tests",
    "vscode-ci",
    "community-export-verification",
    "infrastructure-export-verification",
    "ci-release-boundaries",
)

FORBIDDEN_CURSOR_TOKENS = (
    "cursor-plugin",
    "codestrata-cursor",
    "cursor-ci",
    "cursor-package",
    "cursor-vsix",
)

WORKFLOW_RELATIVE = ".github/workflows/ci.yml"

INTENDED_ENGINE_VERSION = "0.2.0"
INTENDED_VSCODE_VERSION = "0.2.0"
ASSESSMENT_SCHEMA_VERSION = "1.2"

ALLOWED_LIMITATIONS = frozenset(
    {
        "workflows_not_remotely_executed_in_github_actions",
        "provider_plugin_download_may_occur_during_tofu_init",
        "real_remote_infrastructure_repository_absent",
        "production_deployment_workflows_preserved_not_exercised",
        "owner_cutover_deferred",
        "no_live_marketplace_publication",
        "no_final_release_artifact_publication",
        "worktree_may_contain_uncommitted_changes",
        "engine_platform_full_suites_may_be_focused_in_ci",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv129Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = CI_RELEASE_BOUNDARIES_ID
    package_version: str = CI_RELEASE_BOUNDARIES_VERSION
    start_slice_12_10: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True
    no_plan: bool = True
    no_apply: bool = True
    no_destroy: bool = True
    no_aws_credentials_for_validation: bool = True
    assessment_schema_version: str = ASSESSMENT_SCHEMA_VERSION


def default_contract() -> Sv129Contract:
    return Sv129Contract()
