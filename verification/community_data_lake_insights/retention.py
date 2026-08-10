"""Data Lake retention / lifecycle audit."""

from __future__ import annotations

from pathlib import Path

from verification.community_data_lake_insights.contract import LIFECYCLE_TF, VARIABLES_TF
from verification.community_data_lake_insights.helpers import check, read_text
from verification.community_data_lake_insights.models import CheckResult, Defect


def check_retention(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict, list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    lifecycle = read_text(monorepo / LIFECYCLE_TF)
    variables = read_text(monorepo / VARIABLES_TF)

    raw_365 = (
        "accepted_retention_days" in variables
        and "default     = 365" in variables
        and "accepted-retention" in lifecycle
    )
    quarantine_90 = (
        "quarantine_retention_days" in variables
        and "default     = 90" in variables
        and "quarantine-retention" in lifecycle
    )
    checks.append(
        check("retention:raw_365", raw_365, "accepted_retention_days default 365", "retention")
    )
    checks.append(
        check(
            "retention:quarantine_90",
            quarantine_90,
            "quarantine_retention_days default 90",
            "retention",
        )
    )
    if not raw_365:
        defects.append(
            Defect("retention_raw", "retention:raw_365", "365", "mismatch")
        )
    if not quarantine_90:
        defects.append(
            Defect("retention_quarantine", "retention:quarantine_90", "90", "mismatch")
        )

    # identity/ has no lifecycle rule — soft limitation
    identity_lifecycle = "identity" in lifecycle.lower() and "prefix" in lifecycle
    # Look for explicit identity filter — absence is expected
    has_identity_rule = 'prefix = "identity' in lifecycle or "identity/" in lifecycle
    if not has_identity_rule:
        limitations.append("identity_prefix_no_lifecycle")
        checks.append(
            check(
                "retention:identity_no_lifecycle",
                True,
                "identity has no lifecycle (limitation ok)",
                "retention",
            )
        )
    else:
        checks.append(
            check(
                "retention:identity_no_lifecycle",
                False,
                "unexpected identity lifecycle present",
                "retention",
            )
        )

    # Report artifacts lifecycle is a separate module/bucket
    report_mod = monorepo / "infrastructure/modules/community-report-artifacts"
    separate = report_mod.is_dir()
    checks.append(
        check(
            "retention:report_artifacts_separate",
            separate,
            "community-report-artifacts module present",
            "retention",
        )
    )

    summary = {
        "raw_retention_days": 365 if raw_365 else None,
        "quarantine_retention_days": 90 if quarantine_90 else None,
        "identity_lifecycle": has_identity_rule,
        "report_artifacts_separate": separate,
        "append_oriented": True,
        "not_current_previous_limited": True,
        "_identity_lifecycle_noise": identity_lifecycle,
    }
    return checks, defects, summary, limitations
