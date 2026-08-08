"""Platform package inventory checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_auth._common import add_check
from verification.community_insights_auth.contract import AUTH_PACKAGE, AUTH_PACKAGE_FILES
from verification.community_insights_auth.inventory import exists
from verification.community_insights_auth.models import CheckResult, Defect


def check_platform_package(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    add_check(
        checks,
        defects,
        "platform:package",
        exists(monorepo, AUTH_PACKAGE),
        "present",
        "platform",
    )
    for rel in AUTH_PACKAGE_FILES:
        name = rel.rsplit("/", 1)[-1].replace(".py", "")
        add_check(
            checks,
            defects,
            f"platform:file:{name}",
            exists(monorepo, rel),
            "present",
            "platform",
        )
    return checks, defects
