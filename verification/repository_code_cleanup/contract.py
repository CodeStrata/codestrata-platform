"""Contract for Slice 16.3 repository code cleanup verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.repository_code_cleanup import (
    REPOSITORY_CODE_CLEANUP_ID,
    REPOSITORY_CODE_CLEANUP_VERSION,
)

SCHEMA_NAME = "repository-code-cleanup-verification"
SCHEMA_VERSION = "1.0.0"
SV163_OUTPUT_RELATIVE = "reports/verification/sv16-3"
REPORT_JSON = "repository-code-cleanup-verification.json"
REPORT_MD = "repository-code-cleanup-verification.md"

POLICY_ID = "repository-code-cleanup-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "platform/policies/repository_code_cleanup_policy.json"
POLICY_SCHEMA = "repository-code-cleanup-policy:1.0"

CLASSIFICATIONS: tuple[str, ...] = (
    "ACTIVE_KEEP",
    "ACTIVE_RELOCATE_LATER",
    "ACTIVE_DUPLICATE_REMOVE",
    "DEAD_REMOVE",
    "LEGACY_REMOVE",
    "COMPATIBILITY_RETAIN",
    "HISTORICAL_TEST_SUPPORT",
    "GENERATED_NOT_SOURCE",
    "OWNER_REVIEW_REQUIRED",
    "DEFER_TO_REPOSITORY_SPLIT",
    "DEFER_TO_DEPENDENCY_CLEANUP",
    "DEFER_TO_STORAGE_CLEANUP",
)

REMOVED_PATHS: tuple[str, ...] = (
    "engine/src/codestrata/domain/rules/suppression.py",
    "engine/scripts/generate_slice_413.py",
)

REMOVED_SYMBOLS: tuple[tuple[str, str], ...] = (
    ("vscode-plugin/src/engine/discovery.ts", "EngineResolution"),
    ("vscode-plugin/src/engine/discovery.ts", "isExecutablePresent"),
    ("vscode-plugin/src/engine/discovery.ts", "pathEntries"),
    ("vscode-plugin/src/cliDiscovery/compatibility.ts", "MIN_DISCOVERY_CLI_VERSION"),
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv163Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = REPOSITORY_CODE_CLEANUP_ID
    package_version: str = REPOSITORY_CODE_CLEANUP_VERSION
    no_product_semantic_change: bool = True
    production_ingestion_enabled: bool = False
    start_slice_16_4: bool = True
    start_slice_16_5: bool = True
    start_slice_16_6: bool = True
    start_slice_16_7: bool = True
    start_slice_16_8: bool = True
    start_slice_16_9: bool = True
    start_slice_16_10: bool = True
    start_epic_17: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True


def default_contract() -> Sv163Contract:
    return Sv163Contract()
