"""Contract for Slice 17.17."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCHEMA_NAME = "community-telemetry-consent-verification"
SCHEMA_VERSION = "1.0.0"
SUITE_ID = "sv17-17"
SV1717_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-17"
REPORT_JSON = "community-telemetry-consent-verification.json"
REPORT_MD = "community-telemetry-consent-verification.md"

POLICY_RELATIVE = "platform/policies/community_telemetry_consent_validation_policy.json"
POLICY_SCHEMA = "community-telemetry-consent-validation-policy:1.0"
REGISTER_RELATIVE = "platform/policies/community_telemetry_consent_register.json"
REGISTER_SCHEMA = "community-telemetry-consent-register:1.0"
CONTRACT_RELATIVE = "platform/contracts/community_telemetry_consent_verification.json"

DECISIONS_PY = "engine/src/codestrata/telemetry/decisions.py"
CONSENT_PY = "engine/src/codestrata/telemetry/consent.py"
NON_INTERACTIVE_PY = "engine/src/codestrata/telemetry/non_interactive.py"
CLI_CONSENT_PY = "engine/src/codestrata/telemetry/cli_consent.py"
INTERACTIVE_PY = "engine/src/codestrata/telemetry/interactive_consent.py"
RUNTIME_PY = "engine/src/codestrata/telemetry/runtime.py"
TRANSPORT_FACTORY_PY = "engine/src/codestrata/telemetry/transport_factory.py"
ASSESS_CLI_PY = "engine/src/codestrata/cli/assess.py"
REPORT_CLI_PY = "engine/src/codestrata/cli/report.py"
REPORT_PUBLISHING_PY = "engine/src/codestrata/community_cloud/report_publishing.py"
TELEMETRY_CMD_PY = "engine/src/codestrata/cli/telemetry_cmd.py"
PREFERENCES_PY = "engine/src/codestrata/telemetry/preferences.py"
VSCODE_CONSENT_TS = "vscode-plugin/src/telemetry/consent.ts"
VSCODE_PACKAGE_JSON = "vscode-plugin/package.json"
DOCS_TELEMETRY = "docs/reference/telemetry.md"
DOCS_PRIVACY = "docs/security/privacy.md"
DOCS_COMMUNITY_API = "docs/reference/community-api/index.md"
ROUTE_REGISTER = "platform/policies/community_api_route_register.json"
REPORT_PUBLISH_POLICY = "platform/policies/community_report_publishing_policy.json"

EXPECTED_DECISIONS = (
    "disabled_by_default",
    "allowed_for_session",
    "denied_for_session",
    "non_interactive_disabled",
)

POLICY_REQUIRED_VALUES: dict[str, object] = {
    "telemetry_default_posture": "disabled_by_default",
    "explicit_opt_in_required": True,
    "explicit_opt_out_supported": True,
    "non_interactive_never_prompts": True,
    "non_interactive_unknown_privacy_safe": True,
    "assessment_independent_of_telemetry": True,
    "local_report_independent_of_telemetry": True,
    "telemetry_failure_non_blocking": True,
    "telemetry_opt_in_does_not_auto_publish_report": True,
    "historical_data_not_deleted_on_opt_out": True,
    "start_slice_17_17": True,
    "start_slice_17_18": True,
}

SLICE_17_19_PACKAGE_CANDIDATES = (
    "verification/community_production_slice_17_19",
    "verification/community_website_status",
    "verification/community_status_api",
)

# Historical wrong-name candidates (must remain absent).
SLICE_17_18_FORBIDDEN_CANDIDATES = (
    "verification/community_telemetry_consent_17_18",
    "verification/community_production_slice_17_18",
    "verification/community_cloud_share_ui",
)

EXPECTED_17_18_PACKAGE = "verification/community_data_lake_insights"

SOFT_LIMITATION_CODES = frozenset(
    {
        "vscode_full_e2e_deferred_17_21",
        "aggregation_latency",
        "best_effort_telemetry_no_offline_queue",
        "monorepo_pre_cutover_source_authority",
        "worktree_uncommitted",
        "live_datalake_probe_skipped",
        "resolved_by_17_18_http_transport",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1717Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    start_slice_17_17: bool = True
    start_slice_17_18: bool = True


def default_contract() -> Sv1717Contract:
    return Sv1717Contract()
