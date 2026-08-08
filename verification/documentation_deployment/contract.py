"""Contract for Slice 14.12 documentation deployment verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCHEMA_NAME = "documentation-deployment-verification"
SCHEMA_VERSION = "1.0.0"
SV1412_OUTPUT_RELATIVE = "reports/verification/sv14-12"
REPORT_JSON = "documentation-deployment-verification.json"
REPORT_MD = "documentation-deployment-verification.md"

POLICY_ID = "codestrata-documentation-deployment-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "docs/policies/documentation_deployment_policy.json"

DOCS_ROOT = "docs"
ASSETS_DIR = "./.vitepress/dist"
VITEPRESS_OUT = ".vitepress/dist"
WRANGLER_CONFIG = "wrangler.jsonc"
WRANGLER_VERSION = "4.120.0"
VITEPRESS_PIN = "1.6.4"
EXPORT_MANIFEST = "public-export-manifest.yaml"

FORBIDDEN_EPIC_15_PATHS: tuple[str, ...] = (
    "verification/epic15_start",
    "verification/epic_15",
    "tests/verification/epic15_start",
    "reports/verification/sv15-1",
)

ALLOWED_LIMITATIONS: tuple[str, ...] = (
    "no_real_cloudflare_upload_during_verification",
    "cloudflare_dashboard_settings_require_owner_confirmation",
    "dependency_advisories_without_safe_compatible_fix_deferred",
    "one_os_clean_ci_validation",
    "real_cloudflare_auth_not_exercised",
    "worktree_uncommitted",
    "dry_run_requires_node_22",
    "npm_audit_unavailable",
)


@dataclass(frozen=True, slots=True)
class Sv1412Contract:
    """Immutable boundary contract for Slice 14.12."""

    policy_id: str = POLICY_ID
    policy_version: str = POLICY_VERSION
    design_system_version: str = "1.0"
    assessment_schema_version: str = "1.2"
    extension_version: str = "0.2.0"
    no_production_deploy: bool = True
    no_commit: bool = True
    start_epic_15: bool = False


def default_contract() -> Sv1412Contract:
    return Sv1412Contract()


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]
