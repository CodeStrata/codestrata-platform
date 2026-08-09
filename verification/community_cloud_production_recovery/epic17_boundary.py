"""Epic 17 boundary checks for Slice 17.10."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_cloud_production_recovery.contract import (
    CONTRACT_RELATIVE,
    POLICY_RELATIVE,
)
from verification.community_cloud_production_recovery.helpers import add_check, read_json
from verification.community_cloud_production_recovery.models import CheckResult, Defect


def check_epic17_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {
        "start_slice_17_10": True,
        "start_slice_17_11": True,
        "start_slice_17_12": True, "start_slice_17_13": False,
    }

    policy = read_json(monorepo / POLICY_RELATIVE) if (monorepo / POLICY_RELATIVE).is_file() else {}
    contract = read_json(monorepo / CONTRACT_RELATIVE) if (monorepo / CONTRACT_RELATIVE).is_file() else {}
    incremental = monorepo / "platform/policies/community_cloud_incremental_deployment_policy.json"
    incremental_data = read_json(incremental) if incremental.is_file() else {}

    add_check(
        checks,
        defects,
        "boundary:policy_17_10",
        policy.get("start_slice_17_10") is True,
        "true",
        "epic17_boundary",
    )
    add_check(
        checks,
        defects,
        "boundary:policy_17_11",
        policy.get("start_slice_17_11") is True,
        "true",
        "epic17_boundary",
    )
    add_check(
        checks,
        defects,
        "boundary:policy_17_12_false",
        policy.get("start_slice_17_12") is True,
        "false",
        "epic17_boundary",
    )
    add_check(
        checks,
        defects,
        "boundary:contract_17_10",
        contract.get("start_slice_17_10") is True,
        "true",
        "epic17_boundary",
    )
    add_check(
        checks,
        defects,
        "boundary:contract_17_11",
        contract.get("start_slice_17_11") is True,
        "true",
        "epic17_boundary",
    )
    add_check(
        checks,
        defects,
        "boundary:contract_17_12_false",
        contract.get("start_slice_17_12") is True,
        "false",
        "epic17_boundary",
    )
    add_check(
        checks,
        defects,
        "boundary:incremental_17_10",
        incremental_data.get("start_slice_17_10") is True,
        str(incremental_data.get("start_slice_17_10")),
        "epic17_boundary",
    )
    add_check(
        checks,
        defects,
        "boundary:incremental_17_11",
        incremental_data.get("start_slice_17_11") is True,
        str(incremental_data.get("start_slice_17_11")),
        "epic17_boundary",
    )
    add_check(
        checks,
        defects,
        "boundary:incremental_17_12_false",
        incremental_data.get("start_slice_17_12") is False,
        str(incremental_data.get("start_slice_17_12")),
        "epic17_boundary",
    )
    ux_access_policy = monorepo / "platform/policies/community_production_site_ux_access_policy.json"
    add_check(
        checks,
        defects,
        "boundary:slice_17_11_ux_access_policy_present",
        ux_access_policy.is_file(),
        "present",
        "epic17_boundary",
    )
    for candidate in (
        "platform/policies/community_cloud_slice_17_13_policy.json",
        "platform/policies/community_production_slice_17_13_policy.json",
    ):
        add_check(
            checks,
            defects,
            f"boundary:slice_17_13_absent:{Path(candidate).stem}",
            not (monorepo / candidate).exists(),
            "absent",
            "epic17_boundary",
        )

    summary["start_slice_17_10"] = policy.get("start_slice_17_10")
    summary["start_slice_17_11"] = policy.get("start_slice_17_11")
    summary["start_slice_17_12"] = policy.get("start_slice_17_12")
    return checks, defects, summary
