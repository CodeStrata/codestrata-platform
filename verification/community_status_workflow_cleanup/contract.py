"""Contract for Slice 17.25 — Community Status GitHub authority + workflow cleanup."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCHEMA_NAME = "community-status-workflow-cleanup-verification"
SCHEMA_VERSION = "1.0.0"
PACKAGE_ID = "community-status-workflow-cleanup-verification"
VERSION = "1.0.0"
SUITE_ID = "sv17-25"
SV1725_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-25"
REPORT_JSON = "community-status-workflow-cleanup-verification.json"
REPORT_MD = "community-status-workflow-cleanup-verification.md"

POLICY_RELATIVE = "platform/policies/community_status_github_authority_policy.json"
POLICY_SCHEMA = "community-status-github-authority-policy:1.0"
WORKFLOW_REGISTER_RELATIVE = "platform/policies/platform_workflow_authority_register.json"
WORKFLOW_REGISTER_SCHEMA = "platform-workflow-authority-register:1.0"
STATUS_REGISTER_RELATIVE = "platform/policies/community_status_register.json"
STATUS_REGISTER_SCHEMA = "community-status-register:1.1"
CONTRACT_RELATIVE = "platform/contracts/community_status_workflow_cleanup_verification.json"
WORKFLOW_README_RELATIVE = ".github/workflows/README.md"

COMMUNITY_STATUS_DIR = (
    "platform/src/codestrata_platform/community_cloud_api/community_status"
)
COMMUNITY_STATUS_GITHUB = (
    "platform/src/codestrata_platform/community_cloud_api/community_status/github_stars.py"
)
COMMUNITY_STATUS_SERVICE = (
    "platform/src/codestrata_platform/community_cloud_api/community_status/service.py"
)
COMMUNITY_STATUS_MODELS = (
    "platform/src/codestrata_platform/community_cloud_api/community_status/models.py"
)
COMMUNITY_STATUS_ROUTES = (
    "platform/src/codestrata_platform/community_cloud_api/community_status/routes.py"
)
COMMUNITY_CLOUD_APP = "platform/src/codestrata_platform/community_cloud_api/app.py"

DOCS_COMMUNITY_API = "docs/reference/community-api/index.md"
SITE_JS_RELATIVE = "assets/site.js"

EXPECTED_17_24_PACKAGE = "verification/community_insights_production_auth"
EXPECTED_17_25_PACKAGE = "verification/community_status_workflow_cleanup"

SLICE_17_26_PACKAGE_CANDIDATES = (
    "verification/community_epic17_completion",
    "verification/community_release_epic",
    "verification/community_marketplace_publish",
)

PUBLIC_STATUS_URL = "https://api.codestrata.ai/api/v1/community/status"
GITHUB_REPOSITORY = "CodeStrata/codestrata-engine"

ROOT_WORKFLOW_PATHS = (
    ".github/workflows/ci.yml",
    ".github/workflows/aws-identity-check.yml",
    ".github/workflows/infrastructure-plan.yml",
    ".github/workflows/infrastructure-apply.yml",
)

EXPORT_WORKFLOW_PATHS = (
    "insights/.github/workflows/ci.yml",
    "insights/.github/workflows/deploy.yml",
    "infrastructure/.github/workflows/validate.yml",
    "infrastructure/.github/workflows/aws-identity-check.yml",
)

POLICY_REQUIRED_VALUES: dict[str, object] = {
    "community_status_repository_source": "github",
    "community_status_stars_source": "github",
    "community_status_release_source": "github_published_release",
    "community_status_candidate_fallback": True,
    "github_lookup_cached": True,
    "github_lookup_ttl_seconds": 300,
    "github_repository": GITHUB_REPOSITORY,
    "package_version_not_public_sot": True,
    "draft_release_forbidden": True,
    "prerelease_forbidden": True,
    "arbitrary_git_tag_forbidden": True,
    "browser_github_token": False,
    "github_pat_required": False,
    "status_fail_soft": True,
    "marketplace_publish": False,
    "start_slice_17_25": True,
    "start_slice_17_26": False,
}

SOFT_LIMITATION_CODES = frozenset(
    {
        "worktree_uncommitted",
        "monorepo_pre_cutover_authority",
        "github_v0_2_0_release_not_published",
        "live_platform_push_deferred",
        "package_github_release_mismatch",
        "status_api_deploy_pending",
        "github_temporary_unavailable_handled",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


def sibling_site_root(monorepo: Path) -> Path:
    return monorepo.parent / "codestrata-site"


@dataclass(frozen=True, slots=True)
class Sv1725Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    start_slice_17_25: bool = True
    start_slice_17_26: bool = False


def default_contract() -> Sv1725Contract:
    return Sv1725Contract()
