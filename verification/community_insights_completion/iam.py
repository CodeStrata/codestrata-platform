"""IAM boundary gate."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_completion.inventory import add_check, exists, read_text
from verification.community_insights_completion.models import CheckResult, Defect


def check_iam(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(checks, defects, "iam:auth_module", exists(monorepo, "infrastructure/modules/community-insights-auth/main.tf"), "present", "iam")
    tf = read_text(monorepo, "infrastructure/modules/community-insights-auth/main.tf")
    add_check(
        checks,
        defects,
        "iam:scoped_secret_read",
        "secretsmanager:GetSecretValue" in tf and "enable_module == false" in tf,
        "scoped",
        "iam",
    )
    return checks, defects
