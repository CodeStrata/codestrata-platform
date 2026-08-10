"""Individual assessment report checks."""

from __future__ import annotations

from verification.community_22_repository_validation.helpers import add_check
from verification.community_22_repository_validation.models import CheckResult, Defect


def check_reports(*, individual_reports_enabled: bool) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(
        checks,
        defects,
        "reports:individual_enabled",
        individual_reports_enabled is True,
        "true",
        "reports",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    return checks, defects
