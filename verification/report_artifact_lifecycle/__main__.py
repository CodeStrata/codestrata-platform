"""CLI entry for Slice 17.15."""

from __future__ import annotations

from verification.report_artifact_lifecycle.contract import monorepo_root_from_here
from verification.report_artifact_lifecycle.determinism import reports_byte_identical
from verification.report_artifact_lifecycle.reporting import write_report
from verification.report_artifact_lifecycle.runner import build_report, main


def run_with_determinism_check() -> int:
    monorepo = monorepo_root_from_here()
    first = build_report(monorepo)
    second = build_report(monorepo)
    if not reports_byte_identical(first.to_dict(), second.to_dict()):
        raise SystemExit("determinism failure: dual build_report outputs differ")
    path = write_report(monorepo, second)
    rel = path.relative_to(monorepo).as_posix()
    print(f"{second.verdict} checks={second.total_checks} failed={second.failed_checks} report={rel}")
    print(
        f"start_slice_17_15=true start_slice_17_16=true "
        f"engine_lifecycle={second.engine.get('lifecycle')} "
        f"limitations={len(second.limitations)}"
    )
    return 0 if second.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(run_with_determinism_check())
