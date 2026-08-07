"""Contract for Slice 13.9 telemetry consent integration verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.vscode_telemetry_consent_integration import (
    VSCODE_TELEMETRY_CONSENT_INTEGRATION_ID,
    VSCODE_TELEMETRY_CONSENT_INTEGRATION_VERSION,
)

SCHEMA_NAME = "vscode-telemetry-consent-integration-verification"
SCHEMA_VERSION = "1.0.0"
SV139_OUTPUT_RELATIVE = "reports/verification/sv13-9"
REPORT_JSON = "vscode-telemetry-consent-integration-verification.json"
REPORT_MD = "vscode-telemetry-consent-integration-verification.md"

INTEGRATION_POLICY_ID = "community-vscode-telemetry-integration-policy"
INTEGRATION_POLICY_VERSION = "1.0"
RUNTIME_POLICY_ID = "community-vscode-telemetry-runtime-policy"
RUNTIME_POLICY_VERSION = "1.0"
INTENDED_VSCODE_VERSION = "0.2.0"
ASSESSMENT_SCHEMA_VERSION = "1.2"
INTEGRATION_PACKAGE = "vscode-plugin/src/telemetryConsentIntegration"

ALLOWED_LIMITATIONS = frozenset(
    {
        "transport_remains_unavailable",
        "no_production_telemetry_collection",
        "no_full_extension_host_ui_automation",
        "source_locality_verified_in_13_10",
        "marketplace_complete_via_13_12_13_13",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv139Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = VSCODE_TELEMETRY_CONSENT_INTEGRATION_ID
    package_version: str = VSCODE_TELEMETRY_CONSENT_INTEGRATION_VERSION
    start_epic_14: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True


def default_contract() -> Sv139Contract:
    return Sv139Contract()
