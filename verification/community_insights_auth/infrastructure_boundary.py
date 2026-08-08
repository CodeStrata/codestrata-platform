"""Infrastructure boundary checks."""

from __future__ import annotations

import re
from pathlib import Path

from verification.community_insights_auth._common import add_check
from verification.community_insights_auth.contract import INFRA_MODULE
from verification.community_insights_auth.inventory import exists, read_text
from verification.community_insights_auth.models import CheckResult, Defect


def _iam_actions(tf: str) -> str:
    match = re.search(r"actions\s*=\s*\[(.*?)\]", tf, re.DOTALL)
    return match.group(1) if match else ""


def check_infrastructure_boundary(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    tf = read_text(monorepo, f"{INFRA_MODULE}/main.tf")
    actions = _iam_actions(tf)

    add_check(
        checks,
        defects,
        "infra:module_present",
        exists(monorepo, INFRA_MODULE),
        "present",
        "infrastructure_boundary",
    )
    add_check(
        checks,
        defects,
        "infra:enable_module_false",
        "enable_module" in tf and "default     = false" in tf,
        "disabled",
        "infrastructure_boundary",
    )
    add_check(
        checks,
        defects,
        "infra:get_secret_only",
        "GetSecretValue" in actions and "PutSecretValue" not in actions,
        "get_only",
        "infrastructure_boundary",
    )
    add_check(
        checks,
        defects,
        "infra:no_secret_values",
        "password =" not in tf.lower() and "secret_string" not in tf.lower(),
        "ids_only",
        "infrastructure_boundary",
    )
    add_check(
        checks,
        defects,
        "infra:frontend_secrets_empty",
        "frontend_secrets_manager_permissions" in tf,
        "empty",
        "infrastructure_boundary",
    )
    return checks, defects
