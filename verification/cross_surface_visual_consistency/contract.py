"""Contract for Slice 14.13 cross-surface visual consistency."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.cross_surface_visual_consistency import (
    CROSS_SURFACE_CONSISTENCY_ID,
    CROSS_SURFACE_CONSISTENCY_VERSION,
)

SCHEMA_NAME = "cross-surface-visual-consistency-verification"
SCHEMA_VERSION = "1.0.0"
SV1413_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv14-13"
REPORT_JSON = "cross-surface-visual-consistency-verification.json"
REPORT_MD = "cross-surface-visual-consistency-verification.md"

POLICY_ID = "codestrata-cross-surface-consistency-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "design-system/policies/cross_surface_consistency_policy.json"
CONSISTENCY_CONTRACT = "design-system/contracts/cross-surface-consistency.json"
PRESENTATION_CONTRACT = "design-system/contracts/presentation.json"
CONSUMER_MAPPINGS = "design-system/contracts/consumer-mappings.json"
TOKEN_CATALOG = "design-system/tokens/catalog.json"
TOKEN_CSS = "design-system/tokens/tokens.css"

FORBIDDEN_15_7_PATHS: tuple[str, ...] = (
    ".codestrata-artifacts/validation/suites/sv15-7",
)

LEGACY_AMBER_HEX = "#d98a3d"
FORBIDDEN_ACTIVE_IDENTITY = ("AIMF", "Codestrata", "AI Modernization Factory", "Georgia")

ALLOWED_LIMITATIONS: frozenset[str] = frozenset(
    {
        "native_vscode_remains_host_specific",
        "reports_use_offline_font_fallbacks",
        "marketplace_remains_rasterized",
        "no_pixel_perfect_cross_browser_screenshot_comparison",
        "one_chromium_one_os",
        "formal_screen_reader_validation_not_performed",
        "historical_amber_archive_retained",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1413Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = CROSS_SURFACE_CONSISTENCY_ID
    package_version: str = CROSS_SURFACE_CONSISTENCY_VERSION
    start_slice_15_7: bool = False
    no_runtime_behavior_change: bool = True
    no_commit: bool = True


def default_contract() -> Sv1413Contract:
    return Sv1413Contract()
