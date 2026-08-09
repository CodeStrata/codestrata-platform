"""Contract for Slice 16.1 repository inventory verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.repository_inventory import (
    REPOSITORY_INVENTORY_ID,
    REPOSITORY_INVENTORY_VERSION,
)

SCHEMA_NAME = "repository-inventory-verification"
SCHEMA_VERSION = "1.0.0"
SV161_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv16-1"
REPORT_JSON = "repository-inventory-verification.json"
REPORT_MD = "repository-inventory-verification.md"

POLICY_ID = "repository-cleanup-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "platform/policies/repository_cleanup_policy.json"
POLICY_SCHEMA = "repository-cleanup-policy:1.0"

CLASSIFICATIONS: tuple[str, ...] = (
    "ACTIVE_RUNTIME",
    "ACTIVE_DOCUMENTATION",
    "ACTIVE_TEST",
    "ACTIVE_VERIFICATION",
    "ACTIVE_POLICY",
    "ACTIVE_CONTRACT",
    "ACTIVE_ASSET",
    "GENERATED",
    "EXPORT_ONLY",
    "HISTORICAL",
    "LEGACY",
    "STALE",
    "DUPLICATE",
    "ORPHAN",
    "EMPTY",
    "DELETE_CANDIDATE",
    "ARCHIVE_CANDIDATE",
    "OWNER_REVIEW_REQUIRED",
)

INVENTORY_AREAS: tuple[str, ...] = (
    "engine",
    "platform",
    "infrastructure",
    "vscode-plugin",
    "insights",
    "docs",
    "design-system",
    "verification",
    "tests",
    "policies",
    "contracts",
    "reports",
    "generated",
    "assets",
    "build_outputs",
    "export_targets",
    "demo",
    "historical",
    "scripts",
    "governance",
    "knowledge",
    "examples",
    "validation",
)

PRUNE_DIR_NAMES: frozenset[str] = frozenset(
    {
        ".git",
        ".venv",
        "node_modules",
        "__pycache__",
        ".terraform",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".wrangler",
        ".vscode-test",
        "repos",  # validation/repos fixture clones
    }
)

MAX_FILES_PER_AREA = 2500


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv161Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = REPOSITORY_INVENTORY_ID
    package_version: str = REPOSITORY_INVENTORY_VERSION
    audit_only: bool = True
    delete_forbidden: bool = True
    rename_forbidden: bool = True
    move_forbidden: bool = True
    runtime_behavior_change_forbidden: bool = True
    start_slice_16_2: bool = True
    start_slice_16_3: bool = True
    start_slice_16_4: bool = True
    start_slice_16_5: bool = True
    start_slice_16_6: bool = True
    start_slice_16_7: bool = True
    start_slice_16_8: bool = True
    start_slice_16_9: bool = True
    start_slice_16_10: bool = True
    start_epic_17: bool = True
    start_slice_17_2: bool = True
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True


def default_contract() -> Sv161Contract:
    return Sv161Contract()
