"""Documentation boundary gate."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_completion.inventory import add_check, exists
from verification.community_insights_completion.models import CheckResult, Defect


def check_documentation_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(checks, defects, "documentation:data_lake_contract", exists(monorepo, "platform/docs/community-cloud-api/community-data-lake-contract.md"), "present", "documentation_boundary")
    add_check(checks, defects, "documentation:insights_readme", exists(monorepo, "insights/README.md"), "present", "documentation_boundary")
    add_check(checks, defects, "documentation:no_epic16_report", not exists(monorepo, "reports/verification/sv17-1"), "absent", "documentation_boundary")
    return checks, defects
