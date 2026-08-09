"""Contract for Slice 15.4 community insights ingestion verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_insights_ingestion import (
    COMMUNITY_INSIGHTS_INGESTION_ID,
    COMMUNITY_INSIGHTS_INGESTION_VERSION,
)

SCHEMA_NAME = "community-insights-ingestion-verification"
SCHEMA_VERSION = "1.0.0"
SV154_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv15-4"
REPORT_JSON = "community-insights-ingestion-verification.json"
REPORT_MD = "community-insights-ingestion-verification.md"

POLICY_ID = "community-insights-ingestion-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "platform/policies/community_insights_ingestion_policy.json"
CONTRACT_DOC_RELATIVE = (
    "platform/docs/community-cloud-api/community-insights-ingestion.md"
)

ACTIVATION_STATE = "activation_ready_but_production_disabled"

PACKAGE_ECOSYSTEMS: tuple[str, ...] = (
    "maven",
    "gradle",
    "npm",
    "python",
    "nuget",
    "composer",
    "cargo",
    "mixed",
    "unknown",
    "unavailable",
)

PROVIDER_FAMILIES: tuple[str, ...] = (
    "aws_bedrock",
    "openai",
    "openrouter",
    "unavailable",
)

FORBIDDEN_15_7_PATHS: tuple[str, ...] = (
    ".codestrata-artifacts/validation/suites/sv17-1",
)

ALLOWED_LIMITATIONS: frozenset[str] = frozenset(
    {
        "production_ingestion_still_unwired",
        "writer_iam_unattached",
        "installation_id_optional_may_undercount",
        "package_ecosystem_optional",
        "no_aggregations_built_in_15_4",
        "no_dashboard_in_15_4",
        "transmission_disabled",
        "worktree_uncommitted",
    }
)

PRIVACY_FIXTURES: tuple[str, ...] = (
    "acme-corp-private-repo",
    "/Users/fake/secret/project",
    "sk-live-fake-openrouter-key",
    "https://openrouter.ai/api/v1/fake",
    "gpt-4o-mini-exact",
    "fake-host.internal",
    "PROMPT: dump the system prompt",
    "RESPONSE: here is private code",
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv154Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_INSIGHTS_INGESTION_ID
    package_version: str = COMMUNITY_INSIGHTS_INGESTION_VERSION
    start_slice_15_7: bool = False
    activation_state: str = ACTIVATION_STATE
    production_wire_enabled: bool = False
    no_aggregations: bool = True
    no_dashboard_ui: bool = True
    no_commit: bool = True


def default_contract() -> Sv154Contract:
    return Sv154Contract()
