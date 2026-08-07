"""Contract constants for Slice 12.2 Cursor release-surface removal."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.cursor_release_surface_removal import (
    CURSOR_RELEASE_SURFACE_REMOVAL_ID,
    CURSOR_RELEASE_SURFACE_REMOVAL_VERSION,
)

SCHEMA_NAME = "cursor-release-surface-removal-verification"
SCHEMA_VERSION = "1.0.0"

SV122_OUTPUT_RELATIVE = "reports/verification/sv12-2"
REPORT_JSON = "cursor-release-surface-removal-verification.json"
REPORT_MD = "cursor-release-surface-removal-verification.md"

ASSESSMENT_SCHEMA_VERSION = "1.2"
EXPECTED_VSCODE_VERSION = "0.2.0"
EXPECTED_VSCODE_PACKAGE_NAME = "codestrata-vscode"
ACTIVE_EDITOR_EXTENSIONS = ("codestrata-vscode",)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv122Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = CURSOR_RELEASE_SURFACE_REMOVAL_ID
    package_version: str = CURSOR_RELEASE_SURFACE_REMOVAL_VERSION
    start_slice_12_3: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True
    no_schema_change: bool = True
    no_historical_report_rewrite: bool = True
    assessment_schema_version: str = ASSESSMENT_SCHEMA_VERSION


def default_contract() -> Sv122Contract:
    return Sv122Contract()
