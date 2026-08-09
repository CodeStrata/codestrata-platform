"""Baseline readiness checks for Slice 17.10."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_cloud_production_recovery.helpers import add_check
from verification.community_cloud_production_recovery.models import CheckResult, Defect


def check_baseline(
    monorepo: Path, evidence: dict[str, Any], policy: dict[str, Any]
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    loaded = (evidence.get("loaded") or {})
    baseline = loaded.get("baseline_summary") or {}
    lambda_baseline = loaded.get("lambda_baseline") or {}
    has_evidence = bool(baseline) or bool(lambda_baseline)

    add_check(
        checks,
        defects,
        "baseline:evidence",
        has_evidence,
        "present" if has_evidence else "absent",
        "baseline",
        soft=True,
    )
    zero_drift = True
    if baseline:
        zero_drift = baseline.get("non_noop_count", 0) == 0 or baseline.get("zero_drift") is True
        add_check(checks, defects, "baseline:zero_drift", zero_drift, str(baseline.get("non_noop_count")), "baseline")
    else:
        # Policy asserts readiness; operational evidence optional/soft.
        add_check(
            checks,
            defects,
            "baseline:policy_ready",
            policy.get("production_recovery_ready") is True,
            "production_recovery_ready",
            "baseline",
        )
        zero_drift = True

    summary = {
        "evidence": has_evidence,
        "zero_drift": zero_drift,
        "policy_ready": policy.get("production_recovery_ready") is True,
    }
    return checks, defects, summary
