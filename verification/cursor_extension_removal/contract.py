"""Contract constants for Slice 12.1 Cursor extension removal verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.cursor_extension_removal import (
    CURSOR_EXTENSION_REMOVAL_ID,
    CURSOR_EXTENSION_REMOVAL_VERSION,
)

SCHEMA_NAME = "cursor-extension-removal-verification"
SCHEMA_VERSION = "1.0.0"

SV121_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv12-1"
REPORT_JSON = "cursor-extension-removal-verification.json"
REPORT_MD = "cursor-extension-removal-verification.md"

ASSESSMENT_SCHEMA_VERSION = "1.2"
EXPECTED_VSCODE_VERSION = "0.2.0"
EXPECTED_VSCODE_PACKAGE_NAME = "codestrata-vscode"

# Historical client vocabulary retained for schema deserialize (Slice 12.4 Approach A).
HISTORICAL_CURSOR_CLIENT_IDS = (
    "cursor_extension",
)

TRACKED_CURSOR_FILE_COUNT_PRE_REMOVAL = 50
PRODUCT_FILE_COUNT_EXCL_NODE_MODULES_PRE_REMOVAL = 100


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv121Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = CURSOR_EXTENSION_REMOVAL_ID
    package_version: str = CURSOR_EXTENSION_REMOVAL_VERSION
    start_slice_12_2: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True
    no_schema_change: bool = True
    no_historical_report_rewrite: bool = True
    assessment_schema_version: str = ASSESSMENT_SCHEMA_VERSION


def default_contract() -> Sv121Contract:
    return Sv121Contract()
