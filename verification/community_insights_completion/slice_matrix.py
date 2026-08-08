"""Epic 15 slice completion matrix."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_insights_completion.contract import (
    PRIOR_SLICE_RUNNERS,
    SCHEMA_NAME,
    TOTAL_SLICES,
)
from verification.community_insights_completion.models import CheckResult, Defect, SliceRow

SLICE_TITLES: dict[str, str] = {row[0]: row[3] for row in PRIOR_SLICE_RUNNERS}
SLICE_TITLES["15.12"] = "Epic 15 Completion Verification"

SLICE_POLICIES: dict[str, str] = {row[0]: row[4] for row in PRIOR_SLICE_RUNNERS}
SLICE_POLICIES["15.12"] = "community-insights-completion-policy:1.0"

SLICE_SCHEMAS: dict[str, str] = {
    row[0]: f"{row[2]}:1.0.0" for row in PRIOR_SLICE_RUNNERS
}
SLICE_SCHEMAS["15.12"] = f"{SCHEMA_NAME}:1.0.0"

VERIFICATION_DIRS: dict[str, str] = {
    "15.1": "verification/community_data_lake_audit",
    "15.2": "verification/community_analytics_partition",
    "15.3": "verification/community_insights_event_coverage",
    "15.4": "verification/community_insights_ingestion",
    "15.5": "verification/community_insights_query_strategy",
    "15.6": "verification/community_insights_metrics",
    "15.7": "verification/community_insights_aggregation",
    "15.8": "verification/community_insights_application",
    "15.9": "verification/community_insights_auth",
    "15.10": "verification/community_insights_dashboard",
    "15.11": "verification/community_insights_validation",
    "15.12": "verification/community_insights_completion",
}


def build_slice_matrix(
    monorepo: Path,
    *,
    prior_results: dict[str, dict[str, Any]],
    completion_runner_ok: bool,
) -> list[SliceRow]:
    rows: list[SliceRow] = []
    for i in range(1, TOTAL_SLICES + 1):
        sid = f"15.{i}"
        if sid == "15.12":
            status = "pass" if completion_runner_ok else "pending"
            completion = "complete" if completion_runner_ok else "incomplete"
            checks = 0
            failed = 0
            blockers: list[str] = []
            limitations: list[str] = []
        else:
            data = prior_results.get(sid, {})
            verdict = str(data.get("verdict", "missing"))
            if verdict in {"PASS", "PASS_WITH_LIMITATIONS"}:
                status = "pass"
                completion = "complete"
            elif verdict == "missing":
                status = "not_started"
                completion = "incomplete"
            else:
                status = "fail"
                completion = "incomplete"
            checks = int(data.get("total_checks", 0))
            failed = int(data.get("failed_checks", 0))
            blockers = list(data.get("blockers", []))
            limitations = list(data.get("limitations", []))
        pkg = monorepo / VERIFICATION_DIRS[sid]
        if not pkg.is_dir() and sid != "15.12":
            status = "not_started"
            completion = "incomplete"
        rows.append(
            SliceRow(
                slice=sid,
                title=SLICE_TITLES[sid],
                policy=SLICE_POLICIES[sid],
                verification_schema=SLICE_SCHEMAS[sid],
                status=status,
                checks=checks,
                failed_checks=failed,
                blockers=blockers,
                limitations=limitations,
                completion_state=completion,
            )
        )
    return rows


def check_slice_matrix(
    matrix: list[SliceRow],
    *,
    completion_ok: bool,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    checks.append(
        CheckResult(
            "slice_matrix:count_15",
            len(matrix) == TOTAL_SLICES,
            str(len(matrix)),
            "slice_matrix",
        )
    )
    for row in matrix:
        if row.slice == "15.12":
            ok = completion_ok and row.completion_state == "complete"
        else:
            ok = row.completion_state == "complete" and row.status == "pass"
        checks.append(
            CheckResult(
                f"slice_matrix:{row.slice}:complete",
                ok,
                f"{row.status}/{row.completion_state}",
                "slice_matrix",
            )
        )
        if not ok:
            defects.append(
                Defect(
                    "slice_incomplete",
                    row.slice,
                    "complete",
                    row.completion_state,
                )
            )
        if row.status == "not_started":
            defects.append(
                Defect(
                    "slice_not_started",
                    row.slice,
                    "started",
                    "not_started",
                )
            )
    return checks, defects
