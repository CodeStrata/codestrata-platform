"""Contract constants for Slice 9.14 cross-client telemetry privacy verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.privacy_first_telemetry import (
    PRIVACY_FIRST_TELEMETRY_VERIFICATION_ID,
    PRIVACY_FIRST_TELEMETRY_VERIFICATION_VERSION,
)

SCHEMA_NAME = "cross-client-telemetry-privacy-verification"
SCHEMA_VERSION = "1.0.0"

SV914_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv9-14"
REPORT_JSON = "cross-client-telemetry-privacy-verification.json"
REPORT_MD = "cross-client-telemetry-privacy-verification.md"

ENGINE_RUNTIME_POLICY_URN = "community-telemetry-runtime-policy:1.0"
ENGINE_EVENT_SCHEMA_URN = "community-telemetry-runtime-event:1.0"
VSCODE_RUNTIME_POLICY_URN = "community-vscode-telemetry-runtime-policy:1.0"
VSCODE_EVENT_SCHEMA_URN = "community-vscode-telemetry-event-schema:1.0"

ENGINE_CLIENT = "codestrata_cli"
VSCODE_CLIENT = "vscode_extension"

ASSESSMENT_SCHEMA_VERSION = "1.2"


def monorepo_root_from_here() -> Path:
    """Resolve monorepo root from ``verification/privacy_first_telemetry/*.py``."""

    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv914Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = PRIVACY_FIRST_TELEMETRY_VERIFICATION_ID
    package_version: str = PRIVACY_FIRST_TELEMETRY_VERIFICATION_VERSION
    start_slice_915: bool = False
    no_commit: bool = True
    no_shared_runtime_schema: bool = True
    no_http_default: bool = True
    no_vscode_http: bool = True
    no_cursor_telemetry: bool = True
    no_installation_identity: bool = True
    no_persisted_consent: bool = True
    assessment_schema_version: str = ASSESSMENT_SCHEMA_VERSION


def default_contract() -> Sv914Contract:
    return Sv914Contract()
