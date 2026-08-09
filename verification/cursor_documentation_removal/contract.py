"""Contract constants for Slice 12.3 Cursor documentation removal."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.cursor_documentation_removal import (
    CURSOR_DOCUMENTATION_REMOVAL_ID,
    CURSOR_DOCUMENTATION_REMOVAL_VERSION,
)

SCHEMA_NAME = "cursor-documentation-removal-verification"
SCHEMA_VERSION = "1.0.0"

SV123_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv12-3"
REPORT_JSON = "cursor-documentation-removal-verification.json"
REPORT_MD = "cursor-documentation-removal-verification.md"

ASSESSMENT_SCHEMA_VERSION = "1.2"
EXPECTED_VSCODE_VERSION = "0.2.0"

# Active product claim tokens (must not appear as current support).
FORBIDDEN_ACTIVE_CLAIM_PATTERNS: tuple[str, ...] = (
    "/extensions/cursor",
    "codestrata-cursor",
    "`cursor-plugin/`",
    "CodeStrata Cursor Extension ·",
    "| Cursor Extension |",
    "| CodeStrata Cursor / VS Code Extension |",
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv123Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = CURSOR_DOCUMENTATION_REMOVAL_ID
    package_version: str = CURSOR_DOCUMENTATION_REMOVAL_VERSION
    start_slice_12_4: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True
    no_schema_change: bool = True
    no_runtime_change: bool = True
    assessment_schema_version: str = ASSESSMENT_SCHEMA_VERSION


def default_contract() -> Sv123Contract:
    return Sv123Contract()
