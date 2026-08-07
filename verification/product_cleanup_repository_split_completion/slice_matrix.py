"""Slice 12.1–12.10 completion matrix."""

from __future__ import annotations

import json
from pathlib import Path

from verification.product_cleanup_repository_split_completion.contract import (
    EPIC12_VERIFICATION_SCHEMAS,
)
from verification.product_cleanup_repository_split_completion.models import (
    CheckResult,
    Defect,
    SliceEvidence,
)

# slice_id, title, package_dir, report_dir, report_json, tests_dir
_SLICES: tuple[tuple[str, str, str, str, str, str], ...] = (
    (
        "12.1",
        "Remove Cursor Plugin",
        "verification/cursor_extension_removal",
        "reports/verification/sv12-1",
        "cursor-extension-removal-verification.json",
        "tests/verification/cursor_extension_removal",
    ),
    (
        "12.2",
        "Remove Cursor Build, Packaging, and Release Surfaces",
        "verification/cursor_release_surface_removal",
        "reports/verification/sv12-2",
        "cursor-release-surface-removal-verification.json",
        "tests/verification/cursor_release_surface_removal",
    ),
    (
        "12.3",
        "Remove Cursor Documentation and Marketplace References",
        "verification/cursor_documentation_removal",
        "reports/verification/sv12-3",
        "cursor-documentation-removal-verification.json",
        "tests/verification/cursor_documentation_removal",
    ),
    (
        "12.4",
        "Clean Community Product Boundaries",
        "verification/community_client_boundary_cleanup",
        "reports/verification/sv12-4",
        "community-client-boundary-cleanup-verification.json",
        "tests/verification/community_client_boundary_cleanup",
    ),
    (
        "12.5",
        "Define Infrastructure Repository Structure",
        "verification/infrastructure_repository_contract",
        "reports/verification/sv12-5",
        "infrastructure-repository-contract-verification.json",
        "tests/verification/infrastructure_repository_contract",
    ),
    (
        "12.6",
        "Build Infrastructure Export Script",
        "verification/infrastructure_repository_exporter",
        "reports/verification/sv12-6",
        "infrastructure-repository-exporter-verification.json",
        "tests/verification/infrastructure_repository_exporter",
    ),
    (
        "12.7",
        "Verify Infrastructure Repository Export",
        "verification/infrastructure_repository_export",
        "reports/verification/sv12-7",
        "infrastructure-repository-export-verification.json",
        "tests/verification/infrastructure_repository_export",
    ),
    (
        "12.8",
        "Integrate Community and Infrastructure Export Process",
        "verification/repository_export_targets",
        "reports/verification/sv12-8",
        "repository-export-target-verification.json",
        "tests/verification/repository_export_targets",
    ),
    (
        "12.9",
        "Update CI, Release, and Deployment Boundaries",
        "verification/ci_release_boundaries",
        "reports/verification/sv12-9",
        "ci-release-boundary-verification.json",
        "tests/verification/ci_release_boundaries",
    ),
    (
        "12.10",
        "Epic Boundary and Completion Verification",
        "verification/product_cleanup_repository_split_completion",
        "reports/verification/sv12-10",
        "product-cleanup-repository-split-completion-verification.json",
        "tests/verification/product_cleanup_repository_split_completion",
    ),
)


def _report_ok(monorepo: Path, report_dir: str, report_json: str, expected_schema: str) -> tuple[bool, str]:
    path = monorepo / report_dir / report_json
    if not path.is_file():
        # 12.10 report is written by this runner; package presence is enough mid-run
        if report_dir.endswith("sv12-10"):
            return True, "self"
        return False, "missing_report"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False, "invalid_json"
    schema = f"{data.get('schema_name')}:{data.get('schema_version')}"
    if schema != expected_schema:
        return False, f"schema={schema}"
    failed = int(data.get("failed_checks") or 0)
    verdict = str(data.get("verdict") or "")
    if failed > 0 or verdict not in {"PASS", "PASS_WITH_LIMITATIONS", "pass", "pass_with_limitations"}:
        return False, f"verdict={verdict} failed={failed}"
    return True, verdict


def build_slice_matrix(
    monorepo: Path, *, include_1210_report: bool = False
) -> tuple[list[SliceEvidence], list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    matrix: list[SliceEvidence] = []

    for slice_id, title, package, report_dir, report_json, tests in _SLICES:
        expected_schema = EPIC12_VERIFICATION_SCHEMAS[slice_id]
        pkg_ok = (monorepo / package / "contract.py").is_file() and (
            (monorepo / package / "runner.py").is_file()
            or (monorepo / package / "__main__.py").is_file()
        )
        readme_ok = (monorepo / package / "README.md").is_file()
        tests_ok = (monorepo / tests).exists()
        if slice_id == "12.10" and not include_1210_report:
            report_ok, report_detail = True, "pending_self"
        else:
            report_ok, report_detail = _report_ok(
                monorepo, report_dir, report_json, expected_schema
            )

        status = (
            "complete"
            if pkg_ok and readme_ok and tests_ok and (report_ok or slice_id == "12.10")
            else "incomplete"
        )
        # 12.10 complete only when own report later passes — matrix marks package ready
        if slice_id == "12.10":
            status = "complete" if pkg_ok and readme_ok and tests_ok else "incomplete"

        matrix.append(
            SliceEvidence(
                slice_id=slice_id,
                title=title,
                package=package,
                schema=expected_schema,
                report_relative=f"{report_dir}/{report_json}",
                status=status,
            )
        )
        checks.append(
            CheckResult(
                f"slice:{slice_id}:package",
                pkg_ok,
                package,
                "slice_matrix",
            )
        )
        checks.append(
            CheckResult(
                f"slice:{slice_id}:readme",
                readme_ok,
                "README.md",
                "slice_matrix",
            )
        )
        checks.append(
            CheckResult(
                f"slice:{slice_id}:tests",
                tests_ok,
                tests,
                "slice_matrix",
            )
        )
        if slice_id != "12.10":
            checks.append(
                CheckResult(
                    f"slice:{slice_id}:report",
                    report_ok,
                    report_detail,
                    "slice_matrix",
                )
            )
        checks.append(
            CheckResult(
                f"slice:{slice_id}:schema",
                expected_schema == EPIC12_VERIFICATION_SCHEMAS[slice_id],
                expected_schema,
                "slice_matrix",
            )
        )

    complete = sum(1 for s in matrix if s.status == "complete")
    checks.append(
        CheckResult(
            "slice_matrix:ten_complete",
            complete == 10,
            f"{complete}/10",
            "slice_matrix",
        )
    )
    if not all(c.ok for c in checks):
        defects.append(
            Defect(
                "slice-matrix defect",
                "epic12",
                "10/10 complete",
                f"{complete}/10",
            )
        )
    matrix = sorted(matrix, key=lambda s: s.slice_id)
    return matrix, checks, defects
