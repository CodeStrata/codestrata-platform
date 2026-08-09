"""Prior slice regression checks for Slice 17.10."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_cloud_production_recovery.contract import (
    PRIOR_POLICY_INVARIANTS,
    PRIOR_REPORTS,
)
from verification.community_cloud_production_recovery.helpers import add_check, read_json
from verification.community_cloud_production_recovery.models import CheckResult, Defect


def check_prior_slices(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"reports": {}, "invariants": {}, "packages": {}}

    prior_packages = (
        ("17.1", "verification/community_cloud_cicd_architecture"),
        ("17.2", "verification/community_cloud_remote_state"),
        ("17.3", "verification/community_cloud_github_oidc"),
        ("17.4", "verification/community_cloud_production_plan"),
        ("17.5", "verification/community_cloud_infrastructure_deployment"),
        ("17.6", "verification/community_cloud_runtime_security"),
        ("17.7", "verification/community_cloud_production_ingestion"),
        ("17.8", "verification/community_production_sites_deployment"),
        ("17.9", "verification/community_cloud_incremental_deployment"),
    )
    for slice_id, rel in prior_packages:
        path = monorepo / rel
        ok = path.is_dir()
        add_check(checks, defects, f"regression:package_{slice_id}", ok, rel, "prior_slices")
        summary["packages"][slice_id] = ok

    for slice_id, rel in PRIOR_REPORTS:
        path = monorepo / rel
        present = path.is_file()
        verdict = None
        if present:
            data = read_json(path)
            verdict = data.get("verdict")
        pass_like = verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
        add_check(
            checks,
            defects,
            f"regression:report_{slice_id}",
            present and pass_like,
            f"verdict={verdict}" if verdict else "missing",
            "prior_slices",
            soft=present and not pass_like,
        )
        summary["reports"][slice_id] = {"present": present, "verdict": verdict, "pass_like": pass_like}

    for rel, invariants in PRIOR_POLICY_INVARIANTS:
        path = monorepo / rel
        data = read_json(path) if path.is_file() else {}
        for key, expected in invariants.items():
            observed = data.get(key)
            add_check(
                checks,
                defects,
                f"regression:{Path(rel).stem}:{key}",
                observed == expected,
                str(observed),
                "prior_slices",
            )
            summary["invariants"][f"{Path(rel).stem}:{key}"] = observed == expected

    return checks, defects, summary
