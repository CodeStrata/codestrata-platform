"""Contract for Slice 17.20."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCHEMA_NAME = "community-ai-providers-verification"
SCHEMA_VERSION = "1.0.0"
SUITE_ID = "sv17-20"
SV1720_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-20"
REPORT_JSON = "community-ai-providers-verification.json"
REPORT_MD = "community-ai-providers-verification.md"

POLICY_RELATIVE = "platform/policies/community_ai_provider_validation_policy.json"
POLICY_SCHEMA = "community-ai-provider-validation-policy:1.0"
REGISTER_RELATIVE = "platform/policies/community_ai_provider_register.json"
REGISTER_SCHEMA = "community-ai-provider-register:1.0"
CONTRACT_RELATIVE = "platform/contracts/community_ai_providers_verification.json"

ASSESS_AI_PY = "engine/src/codestrata/extensions/assess_ai.py"
FACTORY_PY = "engine/src/codestrata/ai/providers/factory.py"
PROMPT_PY = "engine/src/codestrata/ai/enrichment/prompt.py"
CONTEXT_PY = "engine/src/codestrata/ai/enrichment/context.py"
VALIDATION_PY = "engine/src/codestrata/ai/enrichment/validation.py"
RETRY_POLICY_PY = "engine/src/codestrata/ai/provider_contracts/retry_policy.py"
SETTINGS_PY = "engine/src/codestrata/config/settings.py"
ASSESS_CLI_PY = "engine/src/codestrata/cli/assess.py"
SERVICE_PY = "engine/src/codestrata/application/assessment/service.py"
DOCTOR_PY = "engine/src/codestrata/ai/providers/doctor.py"
AI_ANALYTICS_CATALOGS_PY = (
    "engine/src/codestrata/telemetry/analytics/ai_analytics_catalogs.py"
)
AI_ANALYTICS_PROJECTION_PY = (
    "engine/src/codestrata/telemetry/analytics/ai_analytics_projection.py"
)
DOCS_AI_PROVIDERS = "docs/ai-providers/index.md"
CATALOG_RELATIVE = "validation/repository-catalog/catalog.json"
ASSESSMENTS_RELATIVE = ".codestrata-artifacts/assessments"
WORK_ROOT = Path("/tmp/sv17-20-work")
WORK_ASSESS_OUT = WORK_ROOT / "assess-out"

SUPPORTED_PROVIDERS = ("bedrock", "openai", "openrouter")

POLICY_REQUIRED_VALUES: dict[str, object] = {
    "supported_providers": ["openai", "bedrock", "openrouter"],
    "no_ai_supported": True,
    "deterministic_assessment_provider_independent": True,
    "provider_failure_non_blocking": True,
    "provider_credentials_never_persisted_in_artifacts": True,
    "prompts_responses_excluded_from_telemetry": True,
    "ai_usage_privacy_safe": True,
    "start_slice_17_20": True,
    "start_slice_17_21": True,
}

SLICE_17_22_PACKAGE_CANDIDATES = (
    "verification/community_production_slice_17_22",
    "verification/community_vscode_marketplace_publish",
    "verification/community_status_api",
    "verification/community_website_status",
)

EXPECTED_17_20_PACKAGE = "verification/community_ai_providers"
EXPECTED_17_19_PACKAGE = "verification/community_assessment_engineering_intelligence"
EXPECTED_17_21_PACKAGE = "verification/community_vscode_clean_install"

# Retained alias — 17.21 packages are now allowed; use SLICE_17_22 for forbids.
SLICE_17_21_PACKAGE_CANDIDATES = SLICE_17_22_PACKAGE_CANDIDATES

SOFT_LIMITATION_CODES = frozenset(
    {
        "owner_credential_required_openai",
        "owner_credential_required_openrouter",
        "ai_usage_telemetry_deferred",
        "eir_provider_enrichment_deferred",
        "bounded_representative_repositories",
        "worktree_uncommitted",
        "monorepo_pre_cutover_source_authority",
        "provider_latency_cost_variance",
    }
)

REPRESENTATIVE_PREFERRED = ("flask", "juice-shop", "express")


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1720Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    start_slice_17_20: bool = True
    start_slice_17_21: bool = True
    start_slice_17_22: bool = False


def default_contract() -> Sv1720Contract:
    return Sv1720Contract()
