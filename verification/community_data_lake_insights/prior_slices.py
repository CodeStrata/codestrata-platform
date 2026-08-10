"""Prior slice explanations (17.13 / 17.17) and release corpus deferral."""

from __future__ import annotations

from pathlib import Path

from verification.community_data_lake_insights.helpers import check
from verification.community_data_lake_insights.models import CheckResult, Defect


def check_prior_slices(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict, list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    pkg_17_17 = monorepo / "verification/community_telemetry_consent"
    exists_17_17 = pkg_17_17.is_dir()
    checks.append(
        check(
            "prior_slices:17_17_package_exists",
            exists_17_17,
            "verification/community_telemetry_consent",
            "prior_slices",
        )
    )
    if not exists_17_17:
        defects.append(
            Defect(
                "missing_17_17",
                "prior_slices:17_17_package_exists",
                "present",
                "absent",
            )
        )

    # Historical 17.13 telemetry may be absent — do not fabricate.
    limitations.append("historical_17_13_telemetry_absent")
    checks.append(
        check(
            "prior_slices:17_13_historical_explained",
            True,
            "17.13 telemetry may be absent because transport was unavailable; not fabricated",
            "prior_slices",
        )
    )

    limitations.append("full_22_repo_release_corpus_deferred")
    checks.append(
        check(
            "prior_slices:release_corpus_deferred",
            True,
            "full 22-repo release corpus deferred to Release Epic",
            "prior_slices",
        )
    )

    # Confirm no community status package started
    status_pkgs = (
        monorepo / "verification/community_website_status",
        monorepo / "verification/community_status_api",
    )
    no_status = not any(p.exists() for p in status_pkgs)
    checks.append(
        check(
            "prior_slices:community_status_not_started",
            no_status,
            "community status website feature deferred",
            "prior_slices",
        )
    )

    summary = {
        "slice_17_17_present": exists_17_17,
        "historical_17_13_telemetry_absent": True,
        "full_22_repo_release_corpus_deferred": True,
        "community_status_deferred": no_status,
        "explanation": (
            "Slice 17.13 suite-day telemetry may be absent because the product "
            "default HTTP transport was unavailable; Slice 17.18 proves the path "
            "with new controlled events instead of fabricating history."
        ),
    }
    return checks, defects, summary, limitations
