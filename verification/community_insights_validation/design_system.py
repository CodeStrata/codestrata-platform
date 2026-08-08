"""Design system checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_validation._common import add_check
from verification.community_insights_validation.inventory import exists, load_json, read_text
from verification.community_insights_validation.models import CheckResult, Defect


def check_design_system(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    tokens = read_text(monorepo, "insights/public/design-tokens/tokens.css")
    authoritative = read_text(monorepo, "design-system/tokens/tokens.css")
    add_check(
        checks,
        defects,
        "design:tokens_match",
        bool(tokens) and tokens == authoritative,
        "export_copy",
        "design_system",
    )
    mappings = load_json(monorepo, "design-system/contracts/consumer-mappings.json")
    add_check(
        checks,
        defects,
        "design:consumer_registered",
        "community_insights" in (mappings.get("consumers") or {}),
        "registered",
        "design_system",
    )
    add_check(
        checks,
        defects,
        "design:tokens_file_present",
        exists(monorepo, "insights/public/design-tokens/tokens.css"),
        "present",
        "design_system",
    )
    return checks, defects
