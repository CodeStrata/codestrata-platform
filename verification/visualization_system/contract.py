"""Contract for Slice 14.8."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.visualization_system import VISUALIZATION_ID, VISUALIZATION_VERSION

SCHEMA_NAME = "visualization-system-verification"
SCHEMA_VERSION = "1.0.0"
SV148_OUTPUT_RELATIVE = "reports/verification/sv14-8"
REPORT_JSON = "visualization-system-verification.json"
REPORT_MD = "visualization-system-verification.md"

POLICY_ID = "codestrata-visualization-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "design-system/policies/visualization_policy.json"
VIZ_CONTRACT = "design-system/contracts/visualization.json"
TOKEN_CATALOG = "design-system/tokens/catalog.json"
ASSESSMENT_STYLES = "engine/src/codestrata/reporting/html_v2/styles.py"
ASSESSMENT_RENDERER = "engine/src/codestrata/reporting/html_v2/renderer.py"
EIR_STYLES = (
    "platform/src/codestrata_platform/intelligence_reporting/"
    "presentation/static_html/styles.py"
)
EIR_RENDERER = (
    "platform/src/codestrata_platform/intelligence_reporting/"
    "presentation/static_html/renderer.py"
)

FORBIDDEN_EPIC_15_PATHS = (
    "verification/epic15_start",
    "verification/epic_15",
    "tests/verification/epic15_start",
    "reports/verification/sv15-1",
)

FORBIDDEN_HEALTH_LABELS = ("Healthy", "Passed", "Safe", "Secure")

ALLOWED_LIMITATIONS = frozenset(
    {
        "few_or_no_real_charts_currently_exist",
        "chart_contract_is_foundation_for_future_consumers",
        "browser_screenshot_tooling_may_be_unavailable",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv148Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = VISUALIZATION_ID
    package_version: str = VISUALIZATION_VERSION
    start_epic_15: bool = False
    no_scoring_change: bool = True
    no_commit: bool = True


def default_contract() -> Sv148Contract:
    return Sv148Contract()
