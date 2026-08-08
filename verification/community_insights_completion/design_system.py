"""Design system authority gate."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_completion.contract import DESIGN_SYSTEM_AUTHORITY, POLICY_RELATIVE
from verification.community_insights_completion.inventory import add_check, exists, load_json
from verification.community_insights_completion.models import CheckResult, Defect


def check_design_system(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)
    add_check(checks, defects, "design_system:authority", policy.get("design_system_authority") == DESIGN_SYSTEM_AUTHORITY, str(policy.get("design_system_authority")), "design_system")
    add_check(checks, defects, "design_system:tokens", exists(monorepo, "design-system/tokens/catalog.json"), "present", "design_system")
    add_check(checks, defects, "design_system:insights_tokens", exists(monorepo, "insights/public/design-tokens/tokens.css"), "present", "design_system")
    return checks, defects
