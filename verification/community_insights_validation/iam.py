"""IAM boundary checks."""

from __future__ import annotations

import re
from pathlib import Path

from verification.community_insights_validation._common import add_check
from verification.community_insights_validation.contract import INFRA_MODULE
from verification.community_insights_validation.inventory import exists, read_text
from verification.community_insights_validation.models import CheckResult, Defect


def _iam_actions(tf: str) -> str:
    match = re.search(r"actions\s*=\s*\[(.*?)\]", tf, re.DOTALL)
    return match.group(1) if match else ""


def check_iam(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    tf = read_text(monorepo, f"{INFRA_MODULE}/main.tf")
    actions = _iam_actions(tf)

    add_check(
        checks,
        defects,
        "iam:module_present",
        exists(monorepo, INFRA_MODULE),
        "present",
        "security",
    )
    add_check(
        checks,
        defects,
        "iam:get_secret_only",
        "GetSecretValue" in actions and "PutSecretValue" not in actions,
        "get_only",
        "security",
    )
    add_check(
        checks,
        defects,
        "iam:enable_module_false",
        "enable_module" in tf and "default     = false" in tf,
        "disabled",
        "security",
    )
    return checks, defects
