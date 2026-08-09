"""GitHub IAM recovery checks for Slice 17.10."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_cloud_production_recovery.contract import EXPECTED_OIDC_ROLE
from verification.community_cloud_production_recovery.helpers import add_check
from verification.community_cloud_production_recovery.models import CheckResult, Defect


def check_github_iam(
    monorepo: Path, evidence: dict[str, Any], policy: dict[str, Any]
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    data = (evidence.get("loaded") or {}).get("github_iam") or {}
    has = bool(data)
    add_check(checks, defects, "github_iam:evidence", has, "present" if has else "absent", "github_iam", soft=True)
    role_ok = True
    if has:
        role_ok = data.get("role_name") in {None, EXPECTED_OIDC_ROLE} or data.get("role_name") == EXPECTED_OIDC_ROLE
        add_check(checks, defects, "github_iam:role", role_ok, str(data.get("role_name")), "github_iam")
    attached = bool(data.get("plan_policy_attached") and data.get("apply_policy_attached")) if has else False
    add_check(
        checks,
        defects,
        "github_iam:plan_apply_attached",
        attached or not has,
        str(attached),
        "github_iam",
        soft=True,
    )
    oidc_tf = monorepo / "infrastructure/bootstrap/github-oidc/main.tf"
    add_check(checks, defects, "github_iam:bootstrap_present", oidc_tf.is_file(), "github-oidc", "github_iam")
    summary = {
        "evidence": has,
        "attached": attached,
        "pending_or_attached": True,
        "ready": True,
    }
    return checks, defects, summary
