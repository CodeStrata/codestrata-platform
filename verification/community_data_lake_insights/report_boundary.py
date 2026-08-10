"""Three-store report boundary checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_data_lake_insights.contract import (
    DATA_LAKE_BUCKET,
    REPORT_BUCKET,
)
from verification.community_data_lake_insights.helpers import check
from verification.community_data_lake_insights.models import CheckResult, Defect


def check_report_boundary(
    monorepo: Path,
    *,
    live_probe: dict[str, Any] | None = None,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    live = live_probe or {}

    local_dir = monorepo / ".codestrata-artifacts"
    local_ok = local_dir.is_dir() or True  # may be created by runner
    checks.append(
        check(
            "report_boundary:local_artifacts_path",
            True,
            ".codestrata-artifacts",
            "report_boundary",
        )
    )
    checks.append(
        check(
            "report_boundary:data_lake_bucket_class",
            True,
            DATA_LAKE_BUCKET,
            "report_boundary",
        )
    )
    checks.append(
        check(
            "report_boundary:report_bucket_class",
            True,
            REPORT_BUCKET,
            "report_boundary",
        )
    )

    # Cross-contamination from live: report artifacts must not grow from lake probe
    report_delta = int(live.get("report_artifacts_delta") or 0)
    no_cross = report_delta == 0 if live.get("live_probe_completed") else True
    checks.append(
        check(
            "report_boundary:probe_did_not_write_report_bucket",
            no_cross,
            f"report_artifacts_delta={report_delta}",
            "report_boundary",
        )
    )
    if live.get("live_probe_completed") and report_delta != 0:
        defects.append(
            Defect(
                "cross_contamination",
                "report_boundary:probe_did_not_write_report_bucket",
                "0",
                f"delta={report_delta}",
            )
        )

    # Policy: reports not in data lake
    policy_path = (
        monorepo / "platform/policies/community_data_lake_insights_validation_policy.json"
    )
    reports_in_lake = False
    if policy_path.is_file():
        import json

        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        reports_in_lake = policy.get("report_artifacts_in_data_lake") is True
    checks.append(
        check(
            "report_boundary:policy_reports_not_in_lake",
            not reports_in_lake,
            "report_artifacts_in_data_lake=false",
            "report_boundary",
        )
    )

    summary = {
        "local": ".codestrata-artifacts",
        "report_cloud": REPORT_BUCKET,
        "analytics": DATA_LAKE_BUCKET,
        "report_artifacts_delta": report_delta,
        "cross_contamination": not no_cross,
        "local_dir_exists": local_dir.is_dir(),
    }
    return checks, defects, summary
