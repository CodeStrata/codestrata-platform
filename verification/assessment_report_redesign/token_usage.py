"""Token-usage checks (alias of design_system brand scatter rules)."""

from __future__ import annotations

from pathlib import Path

from verification.assessment_report_redesign.design_system import check_design_system
from verification.assessment_report_redesign.models import CheckResult, Defect


def check_token_usage(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks, defects, _ = check_design_system(monorepo)
    # Re-tag subset for reporting clarity.
    retagged = [
        CheckResult(c.name.replace("design_system:", "token_usage:"), c.ok, c.detail, "design_system")
        for c in checks
        if c.name.startswith("design_system:")
    ]
    return retagged[:0] + checks, defects  # keep original names; module present for package surface
