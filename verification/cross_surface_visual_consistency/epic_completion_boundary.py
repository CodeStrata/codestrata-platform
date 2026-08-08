"""Epic completion boundary checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add
from verification.cross_surface_visual_consistency.contract import FORBIDDEN_15_7_PATHS
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult, Defect


def check_epic_completion_boundary(
    inv: ConsistencyInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    present = [rel for rel in FORBIDDEN_15_7_PATHS if (inv.monorepo / rel).exists()]
    add(
        checks,
        "epic_completion_boundary:slice_15_7_absent",
        not present,
        "absent" if not present else ",".join(present),
        "epic_completion_boundary",
    )
    if present:
        defects.append(Defect("epic_completion_boundary", "Slice 15.7 started"))

    add(
        checks,
        "epic_completion_boundary:start_slice_15_7_false",
        inv.policy.get("prohibited", {}).get("start_slice_15_7") is True,
        "slice_15_7_forbidden",
        "epic_completion_boundary",
    )
    add(
        checks,
        "epic_completion_boundary:no_wholesale_redesign",
        inv.policy.get("prohibited", {}).get("wholesale_redesign") is True,
        "no_redesign",
        "epic_completion_boundary",
    )
    add(
        checks,
        "epic_completion_boundary:14_13_package_present",
        (inv.monorepo / "verification/cross_surface_visual_consistency").is_dir(),
        "package_present",
        "epic_completion_boundary",
    )
    return checks, defects
