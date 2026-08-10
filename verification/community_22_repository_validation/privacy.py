"""Privacy boundary checks."""

from __future__ import annotations

from verification.community_22_repository_validation.helpers import add_check
from verification.community_22_repository_validation.models import CheckResult, Defect


def check_privacy(*, clone_urls_safe: bool) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(
        checks,
        defects,
        "privacy:public_clone_urls",
        clone_urls_safe,
        "credential-free https github URLs",
        "privacy",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    return checks, defects
