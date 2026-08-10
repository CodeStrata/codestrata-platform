"""Contract for Slice 17.16."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCHEMA_NAME = "community-report-publishing-verification"
SCHEMA_VERSION = "1.0.0"
SUITE_ID = "sv17-16"
SV1716_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-16"
REPORT_JSON = "community-report-publishing-verification.json"
REPORT_MD = "community-report-publishing-verification.md"

POLICY_RELATIVE = "platform/policies/community_report_publishing_policy.json"
POLICY_SCHEMA = "community-report-publishing-policy:1.0"
PUBLISHING_REGISTER_RELATIVE = "platform/policies/community_report_publishing_register.json"
PUBLISHING_REGISTER_SCHEMA = "community-report-publishing-register:1.0"
STORAGE_REGISTER_RELATIVE = "platform/policies/community_report_storage_register.json"
STORAGE_REGISTER_SCHEMA = "community-report-storage-register:1.0"
CONTRACT_RELATIVE = "platform/contracts/community_report_publishing_verification.json"

PUBLIC_REPORTS_BASE = "https://reports.codestrata.ai"
PUBLIC_API_BASE = "https://api.codestrata.ai"
DOCS_PAGE_RELATIVE = "docs/reference/community-api/index.md"

REPORTS_MODULE = "infrastructure/modules/community-report-artifacts"
DATA_LAKE_MODULE = "infrastructure/modules/community-data-lake"
PRODUCTION_REPORT_ARTIFACTS_TF = "infrastructure/production/community-report-artifacts.tf"

PLATFORM_REPORTS_IDS = (
    "platform/src/codestrata_platform/community_cloud_api/reports/ids.py"
)
PLATFORM_REPORTS_SANITIZER = (
    "platform/src/codestrata_platform/community_cloud_api/reports/sanitizer.py"
)
PLATFORM_REPORTS_SERVICE = (
    "platform/src/codestrata_platform/community_cloud_api/reports/service.py"
)
PLATFORM_REPORTS_ROUTES = (
    "platform/src/codestrata_platform/community_cloud_api/reports/routes.py"
)
PLATFORM_REPORTS_STORE = (
    "platform/src/codestrata_platform/community_cloud_api/reports/store.py"
)
PLATFORM_REPORTS_POLICY = (
    "platform/src/codestrata_platform/community_cloud_api/reports/policy.py"
)

ENGINE_REPORT_PUBLISHING = "engine/src/codestrata/community_cloud/report_publishing.py"
ENGINE_CLI_REPORT = "engine/src/codestrata/cli/report.py"
ENGINE_ASSESS_SERVICE = "engine/src/codestrata/application/assessment/service.py"

REPORTS_WORKER_DIR = "reports"
REPORTS_WRANGLER = "reports/wrangler.jsonc"
REPORTS_DELIVERY_WORKER = "reports/workers/delivery.ts"

DATA_LAKE_POLICY = "platform/policies/community_data_lake_policy.json"

PRIOR_POLICY_PATHS = (
    "platform/policies/codestrata_report_retention_policy.json",
    "platform/policies/community_api_domain_policy.json",
    "platform/policies/community_report_publishing_policy.json",
)

PRIOR_VERIFICATION_PACKAGES = (
    "verification/report_artifact_lifecycle",
    "verification/community_api_domain",
)

SLICE_17_17_PACKAGE_CANDIDATES = (
    "verification/community_report_publishing_17_17",
    "verification/community_cloud_share_ui",
    "verification/community_production_slice_17_17",
)

POLICY_REQUIRED_VALUES: dict[str, object] = {
    "local_report_always_generated": True,
    "telemetry_opt_in_required_for_cloud_publish": True,
    "explicit_publish_action_required": True,
    "automatic_publish_after_assessment": False,
    "assessment_cloud_versions_per_repository": 2,
    "eir_cloud_versions_per_portfolio": 2,
    "report_artifact_store_separate_from_data_lake": True,
    "report_artifact_store_private": True,
    "raw_s3_urls_public": False,
    "public_report_domain": PUBLIC_REPORTS_BASE,
    "public_ids_opaque": True,
    "public_read": True,
    "publish_authenticated": True,
    "revoke_authenticated": True,
    "revocation_supported": True,
    "start_slice_17_16": True,
    "start_slice_17_17": True,
}

SOFT_LIMITATION_CODES = frozenset(
    {
        "dns_propagation_or_cache_delay",
        "infra_zero_drift_evidence_absent",
        "monorepo_pre_cutover_source_authority",
        "vscode_share_ui_deferred_17_21",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1716Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    start_slice_17_16: bool = True
    start_slice_17_17: bool = True
    public_report_domain: str = PUBLIC_REPORTS_BASE


def default_contract() -> Sv1716Contract:
    return Sv1716Contract()
