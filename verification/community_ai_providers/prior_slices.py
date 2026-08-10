"""Prior slice gates for Slice 17.20 (17.21 allowed; 17.22 forbidden)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_ai_providers.contract import (
    EXPECTED_17_19_PACKAGE,
    EXPECTED_17_21_PACKAGE,
    SLICE_17_22_PACKAGE_CANDIDATES,
)
from verification.community_ai_providers.helpers import check, hard_defect
from verification.community_ai_providers.models import CheckResult, Defect


def check_prior_slices(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    pkg_17_19 = monorepo / EXPECTED_17_19_PACKAGE
    exists_17_19 = pkg_17_19.is_dir()
    checks.append(
        check(
            "prior_slices:17_19_package_exists",
            exists_17_19,
            EXPECTED_17_19_PACKAGE,
            "prior_slices",
        )
    )
    if not exists_17_19:
        defects.append(
            hard_defect(
                "missing_17_19",
                "prior_slices:17_19_package_exists",
                "present",
                "absent",
            )
        )

    pkg_17_21 = monorepo / EXPECTED_17_21_PACKAGE
    checks.append(
        check(
            "prior_slices:17_21_allowed",
            True,
            f"present={pkg_17_21.is_dir()}",
            "prior_slices",
        )
    )

    started_17_22 = any((monorepo / cand).exists() for cand in SLICE_17_22_PACKAGE_CANDIDATES)
    checks.append(
        check(
            "prior_slices:17_22_not_started",
            not started_17_22,
            "no 17.22 packages",
            "prior_slices",
        )
    )
    if started_17_22:
        defects.append(
            hard_defect(
                "slice_17_22_started",
                "prior_slices:17_22_not_started",
                "absent",
                "present",
            )
        )

    corpus_flag = (
        monorepo
        / ".codestrata-artifacts/validation/suites/sv17-20/full-22-corpus-executed.flag"
    )
    no_full_22 = not corpus_flag.exists()
    checks.append(
        check(
            "prior_slices:no_full_22_rerun",
            no_full_22,
            "no sv17-20 full-22 flag",
            "prior_slices",
        )
    )

    status_pkgs = (
        monorepo / "verification/community_website_status",
        monorepo / "verification/community_status_api",
        monorepo / "verification/community_vscode_marketplace_publish",
    )
    status_started = any(p.exists() for p in status_pkgs)
    checks.append(
        check(
            "prior_slices:community_status_deferred",
            not status_started,
            "status packages absent",
            "prior_slices",
        )
    )

    summary = {
        "slice_17_19_present": exists_17_19,
        "slice_17_21_started": pkg_17_21.is_dir(),
        "slice_17_22_started": started_17_22,
        "full_22_rerun": not no_full_22,
        "community_status_deferred": not status_started,
    }
    return checks, defects, summary, limitations
