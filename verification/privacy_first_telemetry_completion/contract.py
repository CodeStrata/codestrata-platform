"""Contract for Epic 9 completion verification (Slice 9.15)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.privacy_first_telemetry_completion import (
    PRIVACY_FIRST_TELEMETRY_COMPLETION_ID,
    PRIVACY_FIRST_TELEMETRY_COMPLETION_VERSION,
)

SCHEMA_NAME = "privacy-first-telemetry-completion-verification"
SCHEMA_VERSION = "1.0.0"

EPIC = "9"
EXPECTED_SLICE_COUNT = 15
SLICES_COMPLETED: tuple[str, ...] = tuple(f"9.{i}" for i in range(1, 16))

SV915_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv9-15"
REPORT_JSON = "privacy-first-telemetry-completion-verification.json"
REPORT_MD = "privacy-first-telemetry-completion-verification.md"

CROSS_CLIENT_REPORT_RELATIVE = (
    ".codestrata-artifacts/validation/suites/sv9-14/cross-client-telemetry-privacy-verification.json"
)
CROSS_CLIENT_SCHEMA = "cross-client-telemetry-privacy-verification"

ASSESSMENT_SCHEMA_VERSION = "1.2"

FORBIDDEN_REPORT_FRAGMENTS: tuple[str, ...] = (
    "/Users/",
    "/home/",
    "file://",
    '"installation_id"',
    '"machineId"',
    '"telemetrySessionId"',
    "Authorization: Bearer",
    "-----BEGIN PRIVATE",
    "AKIA",
)

INTENTIONALLY_EXCLUDED: tuple[str, ...] = (
    "production_telemetry_collection",
    "vscode_http_transport",
    "cursor_telemetry",
    "installation_identity",
    "persisted_consent",
    "queues_workers_batching",
    "endpoint_token_cli_flags",
    "vscode_telemetry_settings",
    "epic_10",
    "commit_tag_publish_deploy",
)

DEFAULT_LIMITATIONS: tuple[str, ...] = (
    "vscode_extension_host_ui_automation_not_required",
    "production_transport_not_operational",
    "cursor_telemetry_out_of_scope",
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv915Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = PRIVACY_FIRST_TELEMETRY_COMPLETION_ID
    package_version: str = PRIVACY_FIRST_TELEMETRY_COMPLETION_VERSION
    epic: str = EPIC
    expected_slice_count: int = EXPECTED_SLICE_COUNT
    slices_completed: tuple[str, ...] = SLICES_COMPLETED
    start_epic_10: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True
    no_shared_runtime_schema: bool = True
    assessment_schema_version: str = ASSESSMENT_SCHEMA_VERSION


def default_contract() -> Sv915Contract:
    return Sv915Contract()
