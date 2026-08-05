"""Community Data Lake completion verification runner (Slice 8.15)."""

from __future__ import annotations

import json
import time
from pathlib import Path

from verification.community_data_lake.contract import COMMUNITY_DATA_LAKE_VERIFICATION_ID
from verification.community_data_lake.runner import run_community_data_lake_verification
from verification.community_data_lake_completion.boundaries import check_boundaries
from verification.community_data_lake_completion.contract import (
    DEFAULT_LIMITATIONS,
    INTEGRATION_REPORT_FILENAME,
    INTENTIONALLY_EXCLUDED,
    SLICES_COMPLETED,
    CompletionVerificationContract,
    default_contract,
)
from verification.community_data_lake_completion.determinism import check_determinism
from verification.community_data_lake_completion.infrastructure import check_infrastructure
from verification.community_data_lake_completion.inventory import (
    build_package_inventory,
    check_package_inventory,
)
from verification.community_data_lake_completion.models import CheckResult, CompletionReport
from verification.community_data_lake_completion.production import check_production
from verification.community_data_lake_completion.reporting import write_completion_report
from verification.community_data_lake_completion.safety import (
    check_integration_report_privacy,
    check_privacy,
)
from verification.community_data_lake_completion.scenarios import (
    build_quarantine_matrix,
    build_stream_matrix,
    check_scenarios,
)
from verification.community_data_lake_completion.storage_contracts import check_storage_contracts
from verification.community_data_lake_completion.versions import (
    build_product_contract_versions,
    build_verification_contract_versions,
    check_versions,
)


def _status_from_checks(checks: list[CheckResult], prefix: str) -> str:
    subset = [
        item
        for item in checks
        if item.category == prefix or item.name.startswith(prefix)
    ]
    if not subset:
        return "unknown"
    return "pass" if all(item.ok for item in subset) else "fail"


def _load_integration_check_count(path: Path) -> int:
    payload = json.loads(path.read_text(encoding="utf-8"))
    summary = payload.get("scenario_summary") or {}
    return int(summary.get("total_checks") or 0)


def _resolve_integration(
    *,
    output_dir: Path,
    run_integration: bool,
) -> tuple[int, list[CheckResult], list[str]]:
    integration_path = output_dir / INTEGRATION_REPORT_FILENAME
    checks: list[CheckResult] = []
    blockers: list[str] = []

    if run_integration:
        integration_report = run_community_data_lake_verification(
            output_dir=output_dir,
            run_opentofu=False,
        )
        count = int(integration_report.scenario_summary.get("total_checks") or 0)
        checks.append(
            CheckResult(
                name="integration:sv9_runner_ok",
                ok=integration_report.ok,
                detail=integration_report.verdict,
                category="integration",
            )
        )
        if not integration_report.ok:
            blockers.append("sv9_integration_verification_failed")
        return count, checks, blockers

    if not integration_path.is_file():
        checks.append(
            CheckResult(
                name="integration:report_present",
                ok=False,
                detail="missing",
                category="integration",
            )
        )
        blockers.append("integration_report_missing")
        return 0, checks, blockers

    payload = json.loads(integration_path.read_text(encoding="utf-8"))
    count = _load_integration_check_count(integration_path)
    checks.append(
        CheckResult(
            name="integration:report_present",
            ok=True,
            detail=f"checks={count}",
            category="integration",
        )
    )
    checks.append(
        CheckResult(
            name="integration:report_schema",
            ok=payload.get("schema_name") == COMMUNITY_DATA_LAKE_VERIFICATION_ID,
            detail=str(payload.get("schema_name")),
            category="integration",
        )
    )
    checks.append(
        CheckResult(
            name="integration:report_ok",
            ok=bool(payload.get("ok")),
            detail=str(payload.get("verdict")),
            category="integration",
        )
    )
    if not payload.get("ok"):
        blockers.append("sv9_integration_report_not_ok")
    checks.extend(check_integration_report_privacy(integration_path))
    return count, checks, blockers


def run_community_data_lake_completion_verification(
    *,
    output_dir: Path | None = None,
    contract: CompletionVerificationContract | None = None,
    run_opentofu: bool = True,
    run_integration: bool = True,
) -> CompletionReport:
    started = time.perf_counter()
    contract = contract or default_contract()
    out = (
        output_dir
        or Path(__file__).resolve().parents[2] / "reports" / "verification"
    ).resolve()
    out.mkdir(parents=True, exist_ok=True)

    checks: list[CheckResult] = []
    checks.extend(check_package_inventory())
    checks.extend(check_boundaries())
    checks.extend(check_versions())
    checks.extend(check_storage_contracts())
    checks.extend(check_scenarios())

    opentofu_status, infra_checks = check_infrastructure(run_opentofu=run_opentofu)
    checks.extend(infra_checks)
    checks.extend(check_production())
    checks.extend(check_determinism())

    integration_count, integration_checks, integration_blockers = _resolve_integration(
        output_dir=out,
        run_integration=run_integration,
    )
    checks.extend(integration_checks)
    checks.extend(check_integration_report_privacy(out / INTEGRATION_REPORT_FILENAME))

    checks.extend(check_privacy(completion_report_path=None))

    failures = [f"{item.name}:{item.detail}" for item in checks if not item.ok]
    by_category: dict[str, int] = {}
    for item in checks:
        by_category[item.category] = by_category.get(item.category, 0) + (
            0 if item.ok else 1
        )

    non_opentofu_failures = [
        f"{item.name}:{item.detail}"
        for item in checks
        if not item.ok and item.category != "opentofu"
    ]
    blockers = list(integration_blockers)
    if non_opentofu_failures:
        blockers.extend(non_opentofu_failures[:12])

    limitations = list(DEFAULT_LIMITATIONS) + list(contract.notes)
    if opentofu_status == "skipped":
        limitations.append("OpenTofu CLI validate skipped by caller.")
    elif opentofu_status == "not_executed_tool_unavailable":
        limitations.append("OpenTofu CLI validation not executed (tool unavailable).")

    ok = not failures and not integration_blockers
    verdict = "pass" if ok else "fail"

    report = CompletionReport(
        ok=ok,
        verdict=verdict,
        slices_completed=SLICES_COMPLETED,
        product_contract_versions=build_product_contract_versions(),
        verification_contract_versions=build_verification_contract_versions(),
        package_inventory=build_package_inventory(),
        stream_matrix=build_stream_matrix(),
        quarantine_matrix=build_quarantine_matrix(),
        storage_abstraction_status=_status_from_checks(checks, "storage"),
        retention_status=_status_from_checks(checks, "infrastructure"),
        encryption_status=_status_from_checks(checks, "infrastructure"),
        access_status=_status_from_checks(checks, "infrastructure"),
        integration_check_count=integration_count,
        production_wiring_status="disabled",
        fail_closed_status=_status_from_checks(checks, "production"),
        privacy_status=_status_from_checks(checks, "privacy"),
        determinism_status=_status_from_checks(checks, "determinism"),
        opentofu_status=opentofu_status if run_opentofu else "skipped",
        blockers=tuple(blockers),
        defects=tuple(failures),
        limitations=tuple(limitations),
        intentionally_excluded=INTENTIONALLY_EXCLUDED,
        checks=tuple(checks),
        scenario_summary={
            "total_checks": len(checks),
            "failed_checks": len(failures),
            **{f"failed_{key}": value for key, value in by_category.items() if value},
        },
        elapsed_ms=(time.perf_counter() - started) * 1000,
    )
    write_completion_report(report, out)
    return report


__all__ = ["run_community_data_lake_completion_verification"]
