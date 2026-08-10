"""CLI entry for Slice 17.14."""

from __future__ import annotations

from verification.community_api_domain.contract import monorepo_root_from_here
from verification.community_api_domain.determinism import reports_byte_identical
from verification.community_api_domain.reporting import write_report
from verification.community_api_domain.runner import build_report, main


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
        f"start_slice_17_14=true start_slice_17_15=false "
        f"authority_modules={len(second.authority.get('modules') or [])} "
        f"routes={second.route_register.get('route_count')}"
    )
    return 0 if second.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(run_with_determinism_check())
