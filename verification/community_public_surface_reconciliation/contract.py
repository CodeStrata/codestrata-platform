"""Contract for Slice 18.6 — Public Surface Reconciliation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCHEMA_NAME = "community-public-surface-reconciliation-verification"
SCHEMA_VERSION = "1.0.0"
PACKAGE_ID = "community-public-surface-reconciliation-verification"
VERSION = "1.0.0"
SUITE_ID = "sv18-6"
SV186_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv18-6"
REPORT_JSON = "community-public-surface-reconciliation-verification.json"
REPORT_MD = "community-public-surface-reconciliation-verification.md"

POLICY_RELATIVE = (
    "platform/policies/community_public_surface_reconciliation_policy.json"
)
CONTRACT_RELATIVE = (
    "platform/contracts/community_public_surface_reconciliation_verification.json"
)
WORKFLOW_REGISTER_RELATIVE = "platform/policies/platform_workflow_authority_register.json"
CLAIM_REGISTER_RELATIVE = (
    "platform/policies/community_public_surface_reconciliation_claim_register.json"
)
CONTRADICTION_REGISTER_RELATIVE = (
    "platform/policies/community_transparency_contradiction_register.json"
)

LANDING_PY = "engine/src/codestrata/cli/landing.py"
CLI_INIT = "engine/src/codestrata/cli/__init__.py"
ASSESS_PY = "engine/src/codestrata/cli/assess.py"
ENGINE_README = "engine/README.md"
ENGINE_SECURITY = "engine/SECURITY.md"
ENGINE_PRIVACY = "engine/PRIVACY.md"
ROOT_SECURITY = "SECURITY.md"
CLI_DOC = "docs/reference/cli.md"
VSCODE_DOC = "docs/extensions/vscode.md"
COMMUNITY_CLOUD_DOC = "docs/architecture/community-cloud.md"
VSCODE_README = "vscode-plugin/README.md"
PACKAGE_INIT = "engine/src/codestrata/__init__.py"
PYPROJECT = "engine/pyproject.toml"

POLICY_REQUIRED_VALUES: dict[str, object] = {
    "bare_cli_truthful": True,
    "installed_version_truthful": True,
    "assessment_path_current": True,
    "telemetry_discoverable": True,
    "telemetry_default_off_clear": True,
    "publish_discoverable": True,
    "publish_separate_from_telemetry": True,
    "ai_optional_clear": True,
    "readme_reconciled": True,
    "security_reconciled": True,
    "privacy_authority_canonical": True,
    "vscode_content_reconciled": True,
    "docs_cli_reconciled": True,
    "docs_vscode_reconciled": True,
    "community_status_version_semantics_clear": True,
    "canonical_domains_only": True,
    "start_slice_18_6": True,
    "start_slice_18_7": False,
    "no_cli_publish": True,
    "no_vscode_marketplace_publish": True,
    "no_release_tag": True,
    "no_full_22_repository_release_corpus": True,
    "no_product_capability_redesign": True,
    "no_telemetry_schema_change": True,
    "no_community_api_redesign": True,
}

FORBIDDEN_18_7_PACKAGES = (
    "verification/community_slice_18_7",
    "verification/community_release_readiness_publication",
    "verification/community_public_transparency_publication",
)

SOFT_LIMITATION_CODES = frozenset(
    {
        "github_release_still_0_1_0",
        "marketplace_content_not_published",
        "website_favicon_deferred",
        "openai_owner_credential_required",
        "openrouter_owner_credential_required",
        "worktree_uncommitted",
        "monorepo_pre_cutover_authority",
        "full_release_corpus_deferred",
    }
)

STALE_PUBLIC_PATTERNS = (
    "--output reports",
    "reports/<repository-name>/<YYYYMMDD",
    "reports/<repo>/<stamp>",
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv186Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    start_slice_18_6: bool = True
    start_slice_18_7: bool = False


def default_contract() -> Sv186Contract:
    return Sv186Contract()
