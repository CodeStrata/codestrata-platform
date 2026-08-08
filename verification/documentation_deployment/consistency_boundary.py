"""Consistency boundary — no 14.13, DS unchanged."""

from __future__ import annotations

import json

from verification.documentation_deployment.contract import FORBIDDEN_EPIC_15_PATHS
from verification.documentation_deployment.inventory import DeploymentInventory
from verification.documentation_deployment.models import CheckResult, Defect


def check_consistency_boundary(
    inv: DeploymentInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "consistency_boundary"))

    markers = [rel for rel in FORBIDDEN_EPIC_15_PATHS if (inv.monorepo / rel).exists()]
    add(
        "consistency_boundary:no_epic_15",
        not markers,
        "absent" if not markers else markers[0],
    )
    add(
        "consistency_boundary:policy_forbids_epic_15",
        inv.policy.get("forbidden", {}).get("start_epic_15") is True,
        "prohibited",
    )

    ds_policy = inv.monorepo / "design-system/policies/design_system_policy.json"
    if ds_policy.is_file():
        ds = json.loads(ds_policy.read_text(encoding="utf-8"))
        add(
            "consistency_boundary:design_system_1_0",
            ds.get("policy_version") == "1.0",
            str(ds.get("policy_version")),
        )
    else:
        add("consistency_boundary:design_system_1_0", False, "missing")

    add(
        "consistency_boundary:expected_unchanged_assessment",
        inv.policy.get("expected_unchanged", {}).get("assessment_schema") == "1.2",
        "1.2",
    )
    add(
        "consistency_boundary:expected_unchanged_extension",
        inv.policy.get("expected_unchanged", {}).get("extension_version") == "0.2.0",
        "0.2.0",
    )

    if markers:
        defects.append(Defect("consistency_boundary", "Epic 15 started prematurely"))
    return checks, defects
