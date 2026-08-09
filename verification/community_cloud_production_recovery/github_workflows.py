"""GitHub workflow recovery checks for Slice 17.10."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_cloud_production_recovery.contract import APPLY_WORKFLOW, PLAN_WORKFLOW
from verification.community_cloud_production_recovery.helpers import add_check, read_text
from verification.community_cloud_production_recovery.models import CheckResult, Defect


def check_github_workflows(
    monorepo: Path, evidence: dict[str, Any]
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    data = (evidence.get("loaded") or {}).get("github_workflow_validation") or {}
    has = bool(data)
    add_check(checks, defects, "github_workflows:evidence", has, "present" if has else "absent", "github_workflows", soft=True)

    plan_text = read_text(monorepo / PLAN_WORKFLOW)
    apply_text = read_text(monorepo / APPLY_WORKFLOW)
    add_check(checks, defects, "github_workflows:plan_exists", bool(plan_text), PLAN_WORKFLOW, "github_workflows")
    add_check(checks, defects, "github_workflows:apply_exists", bool(apply_text), APPLY_WORKFLOW, "github_workflows")
    add_check(
        checks,
        defects,
        "github_workflows:apply_not_on_pr",
        "pull_request:" not in apply_text or data.get("apply_not_on_pr") is True,
        "dispatch_only",
        "github_workflows",
    )
    destroy_gate = (
        data.get("apply_has_destroy_replace_gate") is True
        or "destroy" in apply_text.lower()
        or "replace" in apply_text.lower()
    )
    add_check(checks, defects, "github_workflows:destroy_replace_gate", destroy_gate, "gate", "github_workflows")
    summary = {
        "evidence": has,
        "plan_exists": bool(plan_text),
        "apply_exists": bool(apply_text),
        "destroy_gate": destroy_gate,
    }
    return checks, defects, summary
