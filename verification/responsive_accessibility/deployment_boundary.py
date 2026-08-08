"""Deployment and forward-slice boundary checks."""

from __future__ import annotations

from verification.responsive_accessibility.contract import (
    DEPLOYMENT_PATHS,
    FORBIDDEN_EPIC_15_PATHS,
)
from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "deployment_boundary"


def check_deployment_boundary(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    present_forbidden = [
        path for path in FORBIDDEN_EPIC_15_PATHS if (inv.monorepo / path).exists()
    ]
    add(
        "deployment_boundary:forbidden_14_13_absent",
        not present_forbidden,
        "absent" if not present_forbidden else f"{len(present_forbidden)}",
    )

    deployment_present = [
        path for path in DEPLOYMENT_PATHS if (inv.monorepo / path).exists()
    ]
    add(
        "deployment_boundary:deployment_paths_observed",
        True,
        f"{len(deployment_present)}_present",
    )

    add(
        "deployment_boundary:14_12_deployment_present",
        (inv.monorepo / "verification/documentation_deployment").exists(),
        "present",
    )

    if present_forbidden:
        defects.append(
            Defect("deployment_boundary", "Slice 14.14 artifacts present before authorization")
        )
    return checks, defects
