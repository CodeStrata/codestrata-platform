"""Epic 14 slice completion matrix."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.unified_product_experience_completion.contract import (
    PRIOR_SLICE_RUNNERS,
    SCHEMA_NAME,
    TOTAL_SLICES,
)
from verification.unified_product_experience_completion.models import CheckResult, Defect, SliceRow

SLICE_TITLES: dict[str, str] = {
    row[0]: row[3] for row in PRIOR_SLICE_RUNNERS
}
SLICE_TITLES["14.14"] = "Epic 14 Completion Verification"

SLICE_POLICIES: dict[str, str] = {row[0]: row[4] for row in PRIOR_SLICE_RUNNERS}
SLICE_POLICIES["14.14"] = (
    "codestrata-unified-product-experience-completion-policy:1.0"
)

SLICE_SCHEMAS: dict[str, str] = {
    row[0]: f"{row[2]}:1.0.0" for row in PRIOR_SLICE_RUNNERS
}
SLICE_SCHEMAS["14.14"] = f"{SCHEMA_NAME}:1.0.0"

VERIFICATION_DIRS: dict[str, str] = {
    "14.1": "verification/visual_design_system",
    "14.2": "verification/community_documentation_redesign",
    "14.3": "verification/assessment_report_redesign",
    "14.4": "verification/engineering_intelligence_report_redesign",
    "14.5": "verification/vscode_visual_experience",
    "14.6": "verification/marketplace_visual_assets",
    "14.7": "verification/cross_surface_presentation",
    "14.8": "verification/visualization_system",
    "14.9": "verification/report_navigation_ia",
    "14.10": "verification/brand_assets",
    "14.11": "verification/responsive_accessibility",
    "14.12": "verification/documentation_deployment",
    "14.13": "verification/cross_surface_visual_consistency",
    "14.14": "verification/unified_product_experience_completion",
}


def build_slice_matrix(
    monorepo: Path,
    *,
    prior_results: dict[str, dict[str, Any]],
    completion_runner_ok: bool,
) -> list[SliceRow]:
    rows: list[SliceRow] = []
    for i in range(1, TOTAL_SLICES + 1):
        sid = f"14.{i}"
        if sid == "14.14":
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
        if not pkg.is_dir() and sid != "14.14":
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
            "slice_matrix:count_14",
            len(matrix) == TOTAL_SLICES,
            str(len(matrix)),
            "slice_matrix",
        )
    )
    for row in matrix:
        if row.slice == "14.14":
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
