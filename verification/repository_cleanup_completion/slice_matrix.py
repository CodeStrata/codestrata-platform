"""Live re-run of Slice 16.1–16.9 verifiers into completion matrix."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from verification.repository_cleanup_completion.contract import SLICE_MATRIX
from verification.repository_cleanup_completion.helpers import add_check
from verification.repository_cleanup_completion.models import CheckResult, Defect


def _verdict_of(report: Any) -> str:
    v = getattr(report, "verdict", None)
    if v is None and isinstance(report, dict):
        v = report.get("verdict")
    return str(v or "UNKNOWN")


def _failed_of(report: Any) -> int:
    v = getattr(report, "failed_checks", None)
    if v is None and isinstance(report, dict):
        v = report.get("failed_checks")
    return int(v or 0)


def _limitations_of(report: Any) -> list[str]:
    v = getattr(report, "limitations", None)
    if v is None and isinstance(report, dict):
        v = report.get("limitations") or []
    return list(v or [])


def _build_report_loader(pkg: str) -> Callable[[Path], Any] | None:
    loaders = {
        "repository_inventory": "verification.repository_inventory.runner",
        "repository_documentation": "verification.repository_documentation.runner",
        "repository_code_cleanup": "verification.repository_code_cleanup.runner",
        "repository_asset_design_cleanup": "verification.repository_asset_design_cleanup.runner",
        "repository_dependency_build_cleanup": "verification.repository_dependency_build_cleanup.runner",
        "repository_storage_generated_cleanup": "verification.repository_storage_generated_cleanup.runner",
        "repository_boundary_residency": "verification.repository_boundary_residency.runner",
        "repository_consistency": "verification.repository_consistency.runner",
        "repository_package_release_validation": "verification.repository_package_release_validation.runner",
    }
    mod_name = loaders.get(pkg)
    if not mod_name:
        return None
    import importlib

    mod = importlib.import_module(mod_name)
    return getattr(mod, "build_report")


def check_slice_matrix(
    monorepo: Path,
    *,
    skip_heavy_16_9: bool = False,
) -> tuple[list[CheckResult], list[Defect], list[dict[str, Any]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    matrix: list[dict[str, Any]] = []

    for slice_id, title, pkg, policy, schema in SLICE_MATRIX:
        row: dict[str, Any] = {
            "slice": slice_id,
            "title": title,
            "policy": policy,
            "verification_schema": f"{schema}:1.0.0",
            "package": f"verification/{pkg}",
        }
        pkg_dir = monorepo / "verification" / pkg
        add_check(
            checks,
            defects,
            f"matrix:package_present:{slice_id}",
            pkg_dir.is_dir(),
            pkg,
            "slice_matrix",
            classification="slice_verifier_missing",
        )
        if slice_id == "16.10":
            row.update(
                {
                    "status": "RUNNING",
                    "failed_checks": 0,
                    "blockers": [],
                    "limitations": ["self_completion_gate"],
                    "completion_state": "IN_PROGRESS",
                }
            )
            matrix.append(row)
            continue

        if not pkg_dir.is_dir():
            row.update(
                {
                    "status": "FAIL",
                    "failed_checks": 1,
                    "blockers": ["package_missing"],
                    "limitations": [],
                    "completion_state": "INCOMPLETE",
                }
            )
            matrix.append(row)
            continue

        if skip_heavy_16_9 and slice_id == "16.9":
            # Should not skip in production completion; kept as escape hatch only.
            pass

        loader = _build_report_loader(pkg)
        if loader is None:
            add_check(checks, defects, f"matrix:loader:{slice_id}", False, "no_loader", "slice_matrix")
            row.update(
                {
                    "status": "FAIL",
                    "failed_checks": 1,
                    "blockers": ["no_loader"],
                    "limitations": [],
                    "completion_state": "INCOMPLETE",
                }
            )
            matrix.append(row)
            continue

        try:
            report = loader(monorepo)
            verdict = _verdict_of(report)
            failed = _failed_of(report)
            limitations = sorted(_limitations_of(report))
            ok = verdict in {"PASS", "PASS_WITH_LIMITATIONS"} and failed == 0
            add_check(
                checks,
                defects,
                f"matrix:live_rerun:{slice_id}",
                ok,
                f"verdict={verdict} failed={failed}",
                "slice_matrix",
                classification="slice_verifier_failed",
            )
            row.update(
                {
                    "status": verdict,
                    "failed_checks": failed,
                    "blockers": [] if ok else [f"verdict={verdict}"],
                    "limitations": limitations,
                    "completion_state": "COMPLETE" if ok else "INCOMPLETE",
                }
            )
        except Exception as exc:  # noqa: BLE001
            add_check(
                checks,
                defects,
                f"matrix:live_rerun:{slice_id}",
                False,
                type(exc).__name__,
                "slice_matrix",
                classification="slice_verifier_failed",
            )
            row.update(
                {
                    "status": "FAIL",
                    "failed_checks": 1,
                    "blockers": [type(exc).__name__],
                    "limitations": [],
                    "completion_state": "INCOMPLETE",
                }
            )
        matrix.append(row)

    complete = sum(1 for r in matrix if r.get("completion_state") in {"COMPLETE", "IN_PROGRESS"})
    add_check(
        checks,
        defects,
        "matrix:ten_of_ten",
        len(matrix) == 10 and complete == 10,
        f"rows={len(matrix)} completeish={complete}",
        "slice_matrix",
        classification="matrix_incomplete",
    )
    return checks, defects, matrix
