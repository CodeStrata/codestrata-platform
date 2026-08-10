"""Portfolio identity helpers for Slice 17.19."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_assessment_engineering_intelligence.contract import (
    INTELLIGENCE_RELATIVE,
    PORTFOLIO_ID,
)
from verification.community_assessment_engineering_intelligence.helpers import check
from verification.community_assessment_engineering_intelligence.models import (
    CheckResult,
    Defect,
)


def check_portfolio(
    monorepo: Path,
    *,
    eir_generation: dict[str, Any] | None = None,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    gen = eir_generation or {}
    portfolio_id = str(gen.get("portfolio_id") or PORTFOLIO_ID)
    current = monorepo / INTELLIGENCE_RELATIVE / portfolio_id / "current"
    exists = current.is_dir()
    checks.append(
        check(
            "portfolio:stable_id",
            portfolio_id == PORTFOLIO_ID,
            portfolio_id,
            "portfolio",
        )
    )
    checks.append(
        check(
            "portfolio:current_present",
            exists or bool(gen.get("generated")),
            str(current.relative_to(monorepo)) if exists else "pending_generation",
            "portfolio",
        )
    )
    summary = {
        "portfolio_id": PORTFOLIO_ID,
        "current_relative": (
            str(current.relative_to(monorepo)) if exists else None
        ),
        "stable": portfolio_id == PORTFOLIO_ID,
    }
    return checks, defects, summary
