"""Live re-run of Slice 10.8 anonymous analytics privacy verification (Slice 10.9).

Per the Slice 10.9 brief, the stale Slice 10.8 report is never trusted alone;
this module re-invokes ``run_anonymous_analytics_privacy_verification`` live
and asserts pass / 157 checks / 0 defects.
"""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_completion.contract import (
    PRIVACY_EXPECTED_CHECKS,
    PRIVACY_SCHEMA,
)
from verification.anonymous_analytics_completion.models import CheckResult, Defect
from verification.anonymous_analytics_privacy.runner import (
    run_anonymous_analytics_privacy_verification,
)


def check_privacy_verification(
    monorepo: Path,
    *,
    write_report: bool = True,
) -> tuple[list[CheckResult], list[Defect], str]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    report = run_anonymous_analytics_privacy_verification(
        monorepo=monorepo,
        write_report=write_report,
    )

    checks.append(
        CheckResult(
            "privacy_verification:schema_name",
            ok=report.schema_name == PRIVACY_SCHEMA,
            detail=report.schema_name,
            category="privacy_verification",
        )
    )
    checks.append(
        CheckResult(
            "privacy_verification:schema_version_1_0_0",
            ok=report.schema_version == "1.0.0",
            detail=report.schema_version,
            category="privacy_verification",
        )
    )
    checks.append(
        CheckResult(
            "privacy_verification:verdict_pass",
            ok=report.verdict == "pass",
            detail=report.verdict,
            category="privacy_verification",
        )
    )
    checks.append(
        CheckResult(
            "privacy_verification:checks_157",
            ok=report.total_checks == PRIVACY_EXPECTED_CHECKS,
            detail=str(report.total_checks),
            category="privacy_verification",
        )
    )
    checks.append(
        CheckResult(
            "privacy_verification:zero_failed",
            ok=report.failed_checks == 0,
            detail=str(report.failed_checks),
            category="privacy_verification",
        )
    )
    checks.append(
        CheckResult(
            "privacy_verification:zero_defects",
            ok=len(report.defects) == 0,
            detail=str(len(report.defects)),
            category="privacy_verification",
        )
    )
    checks.append(
        CheckResult(
            "privacy_verification:zero_blockers",
            ok=len(report.blockers) == 0,
            detail=str(len(report.blockers)),
            category="privacy_verification",
        )
    )

    for item in checks:
        if not item.ok:
            defects.append(
                Defect(
                    "privacy defect",
                    item.name,
                    "pass",
                    "fail",
                    detail=item.detail,
                )
            )

    status = "pass" if all(c.ok for c in checks) else "fail"
    return checks, defects, status
