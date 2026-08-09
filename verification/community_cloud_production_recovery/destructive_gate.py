"""Destructive plan gate for Slice 17.10."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_cloud_production_recovery.contract import FIXTURES_RELATIVE
from verification.community_cloud_production_recovery.helpers import (
    add_check,
    evaluate_destructive_gate,
    read_json,
)
from verification.community_cloud_production_recovery.models import CheckResult, Defect


def check_destructive_gate(
    monorepo: Path, evidence: dict[str, Any], policy: dict[str, Any]
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    fixtures = monorepo / FIXTURES_RELATIVE
    destroy = read_json(fixtures / "plan_destroy.json") if (fixtures / "plan_destroy.json").is_file() else {}
    replace = read_json(fixtures / "plan_replace.json") if (fixtures / "plan_replace.json").is_file() else {}
    inplace = read_json(fixtures / "plan_inplace_update.json") if (fixtures / "plan_inplace_update.json").is_file() else {}

    add_check(checks, defects, "destructive_gate:fixtures", bool(destroy and replace and inplace), "fixtures", "destructive_gate")
    add_check(
        checks,
        defects,
        "destructive_gate:policy",
        policy.get("destructive_plan_gate") is True,
        "true",
        "destructive_gate",
    )

    d_eval = evaluate_destructive_gate(destroy) if destroy else {"blocked": False, "allowed": False}
    r_eval = evaluate_destructive_gate(replace) if replace else {"blocked": False, "allowed": False}
    i_eval = evaluate_destructive_gate(inplace) if inplace else {"blocked": True, "allowed": False}

    add_check(checks, defects, "destructive_gate:destroy_blocked", d_eval.get("blocked") is True, str(d_eval), "destructive_gate")
    add_check(checks, defects, "destructive_gate:replace_blocked", r_eval.get("blocked") is True, str(r_eval), "destructive_gate")
    add_check(
        checks,
        defects,
        "destructive_gate:inplace_allowed",
        i_eval.get("allowed") is True and i_eval.get("blocked") is False,
        str(i_eval),
        "destructive_gate",
    )

    # Optional live evidence
    live = (evidence.get("loaded") or {}).get("destructive_gate") or {}
    if live:
        add_check(
            checks,
            defects,
            "destructive_gate:live",
            live.get("destroy_blocked") is True and live.get("replace_blocked") is True,
            "live",
            "destructive_gate",
        )

    # Data lake / remote state destroy forbidden by policy
    add_check(
        checks,
        defects,
        "destructive_gate:data_lake_destroy_forbidden",
        policy.get("data_lake_destroy_forbidden") is True,
        "true",
        "destructive_gate",
    )
    add_check(
        checks,
        defects,
        "destructive_gate:remote_state_destroy_forbidden",
        policy.get("remote_state_destroy_forbidden") is True,
        "true",
        "destructive_gate",
    )

    summary = {
        "destroy_blocked": d_eval.get("blocked") is True,
        "replace_blocked": r_eval.get("blocked") is True,
        "inplace_allowed": i_eval.get("allowed") is True,
        "gate_ready": policy.get("destructive_plan_gate") is True,
    }
    return checks, defects, summary
