"""Contract for Slice 13.7 VS Code HTML report opening verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.vscode_html_report_opening import (
    VSCODE_HTML_REPORT_OPENING_ID,
    VSCODE_HTML_REPORT_OPENING_VERSION,
)

SCHEMA_NAME = "vscode-html-report-opening-verification"
SCHEMA_VERSION = "1.0.0"
SV137_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv13-7"
REPORT_JSON = "vscode-html-report-opening-verification.json"
REPORT_MD = "vscode-html-report-opening-verification.md"

REPORT_POLICY_ID = "community-vscode-report-opening-policy"
REPORT_POLICY_VERSION = "1.0"
INTENDED_VSCODE_VERSION = "0.2.0"
ASSESSMENT_SCHEMA_VERSION = "1.2"
REPORT_PACKAGE = "vscode-plugin/src/reportOpening"

ALLOWED_LIMITATIONS = frozenset(
    {
        "prompt_driven_open_retained",
        "stale_certainty_limited_to_engine_run_directory",
        "symlink_junction_partially_mock_validated",
        "system_browser_not_launched_in_tests",
        "recovery_framework_available_via_13_8",
        "no_full_extension_host_ui_automation",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv137Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = VSCODE_HTML_REPORT_OPENING_ID
    package_version: str = VSCODE_HTML_REPORT_OPENING_VERSION
    start_epic_14: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True


def default_contract() -> Sv137Contract:
    return Sv137Contract()
