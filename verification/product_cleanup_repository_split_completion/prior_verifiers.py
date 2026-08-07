"""Re-invoke or consume prior Epic 12 verifiers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from verification.product_cleanup_repository_split_completion.models import (
    CheckResult,
    Defect,
)


def _verdict_ok(report: Any) -> bool:
    verdict = getattr(report, "verdict", None)
    if verdict is None and isinstance(report, dict):
        verdict = report.get("verdict")
    failed = getattr(report, "failed_checks", None)
    if failed is None and isinstance(report, dict):
        failed = report.get("failed_checks")
    failed_i = int(failed or 0)
    return failed_i == 0 and str(verdict) in {
        "PASS",
        "PASS_WITH_LIMITATIONS",
        "pass",
        "pass_with_limitations",
    }


def _consume_report(
    monorepo: Path, relative: str, expected_schema_name: str
) -> tuple[bool, str]:
    path = monorepo / relative
    if not path.is_file():
        return False, "missing"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_name") != expected_schema_name:
        return False, "schema_mismatch"
    if int(data.get("failed_checks") or 0) > 0:
        return False, "failed_checks"
    if str(data.get("verdict")) not in {
        "PASS",
        "PASS_WITH_LIMITATIONS",
        "pass",
        "pass_with_limitations",
    }:
        return False, str(data.get("verdict"))
    return True, str(data.get("verdict"))


def invoke_prior_verifiers(
    monorepo: Path,
    *,
    rerun_expensive: bool = True,
) -> tuple[dict[str, str], list[CheckResult], list[Defect]]:
    """Re-run authoritative verifiers where practical; consume 12.7 if skip flag."""
    statuses: dict[str, str] = {}
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    runners: list[tuple[str, str, Callable[[], Any]]] = []

    def add(slice_id: str, schema: str, fn: Callable[[], Any]) -> None:
        runners.append((slice_id, schema, fn))

    # Lightweight / authoritative re-runs
    from verification.ci_release_boundaries.runner import run as run_129
    from verification.repository_export_targets.runner import run as run_128

    add("12.8", "repository-export-target-verification", lambda: run_128(monorepo))
    add("12.9", "ci-release-boundary-verification", lambda: run_129(monorepo))

    from verification.infrastructure_repository_contract.runner import (
        run_infrastructure_repository_contract_verification,
    )

    add(
        "12.5",
        "infrastructure-repository-contract-verification",
        lambda: run_infrastructure_repository_contract_verification(monorepo=monorepo),
    )

    from verification.infrastructure_repository_exporter.runner import run as run_126

    add(
        "12.6",
        "infrastructure-repository-exporter-verification",
        lambda: run_126(monorepo),
    )

    from verification.community_client_boundary_cleanup.runner import (
        run_community_client_boundary_cleanup_verification,
    )

    add(
        "12.4",
        "community-client-boundary-cleanup-verification",
        lambda: run_community_client_boundary_cleanup_verification(monorepo=monorepo),
    )

    from verification.cursor_documentation_removal.runner import (
        run_cursor_documentation_removal_verification,
    )

    add(
        "12.3",
        "cursor-documentation-removal-verification",
        lambda: run_cursor_documentation_removal_verification(monorepo=monorepo),
    )

    from verification.cursor_release_surface_removal.runner import (
        run_cursor_release_surface_removal_verification,
    )

    add(
        "12.2",
        "cursor-release-surface-removal-verification",
        lambda: run_cursor_release_surface_removal_verification(monorepo=monorepo),
    )

    from verification.cursor_extension_removal.runner import (
        run_cursor_extension_removal_verification,
    )

    add(
        "12.1",
        "cursor-extension-removal-verification",
        lambda: run_cursor_extension_removal_verification(
            monorepo=monorepo,
            run_vscode_compile=False,
            run_vscode_tests=False,
        ),
    )

    for slice_id, schema, fn in runners:
        try:
            report = fn()
            ok = _verdict_ok(report)
            statuses[slice_id] = "pass" if ok else "fail"
            checks.append(
                CheckResult(
                    f"prior:{slice_id}:rerun",
                    ok,
                    schema,
                    "prior_verifiers",
                )
            )
            if not ok:
                defects.append(
                    Defect(
                        "slice-matrix defect",
                        slice_id,
                        "PASS*",
                        str(getattr(report, "verdict", "fail")),
                    )
                )
        except Exception as exc:  # noqa: BLE001 — surface as check failure
            statuses[slice_id] = "error"
            checks.append(
                CheckResult(
                    f"prior:{slice_id}:rerun",
                    False,
                    type(exc).__name__,
                    "prior_verifiers",
                )
            )
            defects.append(
                Defect("harness defect", slice_id, "rerun_ok", type(exc).__name__)
            )

    # Slice 12.7 — re-run dual export + OpenTofu when requested
    if rerun_expensive:
        try:
            from verification.infrastructure_repository_export.runner import run as run_127

            report = run_127(monorepo)
            ok = _verdict_ok(report)
            statuses["12.7"] = "pass" if ok else "fail"
            checks.append(
                CheckResult(
                    "prior:12.7:rerun",
                    ok,
                    "infrastructure-repository-export-verification",
                    "prior_verifiers",
                )
            )
            if not ok:
                defects.append(
                    Defect(
                        "exported-repository defect",
                        "12.7",
                        "PASS*",
                        str(getattr(report, "verdict", "fail")),
                    )
                )
        except Exception as exc:  # noqa: BLE001
            statuses["12.7"] = "error"
            checks.append(
                CheckResult(
                    "prior:12.7:rerun",
                    False,
                    type(exc).__name__,
                    "prior_verifiers",
                )
            )
            defects.append(
                Defect("harness defect", "12.7", "rerun_ok", type(exc).__name__)
            )
    else:
        ok, detail = _consume_report(
            monorepo,
            "reports/verification/sv12-7/infrastructure-repository-export-verification.json",
            "infrastructure-repository-export-verification",
        )
        statuses["12.7"] = "pass" if ok else "fail"
        checks.append(
            CheckResult("prior:12.7:consume", ok, detail, "prior_verifiers")
        )
        if not ok:
            defects.append(
                Defect("exported-repository defect", "12.7", "PASS*", detail)
            )

    return statuses, checks, defects
