"""Contract for Slice 17.18."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCHEMA_NAME = "community-data-lake-insights-verification"
SCHEMA_VERSION = "1.0.0"
SUITE_ID = "sv17-18"
SV1718_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-18"
REPORT_JSON = "community-data-lake-insights-verification.json"
REPORT_MD = "community-data-lake-insights-verification.md"

POLICY_RELATIVE = "platform/policies/community_data_lake_insights_validation_policy.json"
POLICY_SCHEMA = "community-data-lake-insights-validation-policy:1.0"
STREAM_REGISTER = "platform/policies/community_data_lake_stream_register.json"
AGG_REGISTER = "platform/policies/community_insights_aggregation_register.json"
CONTRACT_RELATIVE = "platform/contracts/community_data_lake_insights_verification.json"

PRODUCT_TRANSPORT_PY = "engine/src/codestrata/telemetry/product_transport.py"
PROMPT_RUNTIME_FACTORY_PY = "engine/src/codestrata/telemetry/prompt_runtime_factory.py"
RUNTIME_FACTORY_PY = "engine/src/codestrata/telemetry/runtime_factory.py"
PARTITIONS_PY = (
    "platform/src/codestrata_platform/community_cloud_api/data_lake/partitions.py"
)
ENUMS_PY = "platform/src/codestrata_platform/community_cloud_api/data_lake/enums.py"
READER_PY = (
    "platform/src/codestrata_platform/community_cloud_api/insights_storage/reader.py"
)
INSIGHTS_MODELS_PY = (
    "platform/src/codestrata_platform/community_cloud_api/insights_query/models.py"
)
DEPLOYMENT_WIRING_PY = (
    "platform/src/codestrata_platform/community_cloud_api/deployment/wiring.py"
)
LIFECYCLE_TF = "infrastructure/modules/community-data-lake/lifecycle.tf"
VARIABLES_TF = "infrastructure/modules/community-data-lake/variables.tf"
METRICS_POLICY = "platform/policies/community_insights_metrics_policy.json"
QUERY_POLICY = "platform/policies/community_insights_query_policy.json"
DOCS_PRIVACY = "docs/security/privacy.md"
DOCS_COMMUNITY_API = "docs/reference/community-api/index.md"
CREDENTIAL_FILE_RELATIVE = "infrastructure/production/.local/sv17-16-e2e.client.token"

DATA_LAKE_BUCKET = "codestrata-community-data-lake-production"
REPORT_BUCKET = "codestrata-community-report-artifacts-production"
API_BASE = "https://api.codestrata.ai"
INSIGHTS_BASE = "https://insights.codestrata.ai"
AWS_PROFILE = "codestrata_infra"
AWS_REGION = "us-west-2"

POLICY_REQUIRED_VALUES: dict[str, object] = {
    "production_http_transport_available_after_opt_in": True,
    "live_datalake_probe_completed": True,
    "data_lake_append_oriented": True,
    "report_artifacts_in_data_lake": False,
    "insights_reads_production_data_lake": True,
    "query_budget_reached_false_for_supported_window": True,
    "private_payload_not_exposed": True,
    "quarantine_behavior": "http_reject_before_persist",
    "start_slice_17_18": True,
    "start_slice_17_19": True,
}

EXPECTED_17_19_PACKAGE = "verification/community_assessment_engineering_intelligence"

# Forbidden wrong names for 17.19 plus any premature 17.20 packages.
SLICE_17_19_PACKAGE_CANDIDATES = (
    "verification/community_production_slice_17_19",
    "verification/community_website_status",
    "verification/community_status_api",
)

SLICE_17_20_PACKAGE_CANDIDATES = (
    "verification/community_production_slice_17_20",
    "verification/community_status_api",
    "verification/community_website_status",
)

SOFT_LIMITATION_CODES = frozenset(
    {
        "historical_17_13_telemetry_absent",
        "full_22_repo_release_corpus_deferred",
        "low_synthetic_data_volume",
        "aggregation_latency",
        "worktree_uncommitted",
        "monorepo_pre_cutover_source_authority",
        "identity_prefix_no_lifecycle",
    }
)

PROBE_STREAMS = (
    "telemetry",
    "assessment_metadata",
    "cli_event",
    "ai_usage",
)

STREAM_ENDPOINTS: dict[str, str] = {
    "telemetry": "/api/v1/telemetry",
    "assessment_metadata": "/api/v1/assessment-metadata",
    "cli_event": "/api/v1/cli-events",
    "ai_usage": "/api/v1/ai-usage",
}

EXPECTED_SECTIONS = (
    "Activity",
    "Assessments",
    "Adoption",
    "Coverage",
    "Technology",
    "AI",
    "Validation",
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1718Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    start_slice_17_18: bool = True
    start_slice_17_19: bool = True


def default_contract() -> Sv1718Contract:
    return Sv1718Contract()
