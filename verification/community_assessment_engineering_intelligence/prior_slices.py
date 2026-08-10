"""Prior slice gates for Slice 17.19 (allows 17.20; forbids 17.21)."""

from __future__ import annotations

from pathlib import Path

from verification.community_assessment_engineering_intelligence.contract import (
    EXPECTED_17_20_PACKAGE,
    SLICE_17_21_PACKAGE_CANDIDATES,
)
from verification.community_assessment_engineering_intelligence.helpers import (
    check,
    hard_defect,
)
from verification.community_assessment_engineering_intelligence.models import (
    CheckResult,
    Defect,
)


def check_prior_slices(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict, list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    pkg_17_18 = monorepo / "verification/community_data_lake_insights"
    exists_17_18 = pkg_17_18.is_dir()
    checks.append(
        check(
            "prior_slices:17_18_package_exists",
            exists_17_18,
            "verification/community_data_lake_insights",
            "prior_slices",
        )
    )
    if not exists_17_18:
        defects.append(
            hard_defect(
                "missing_17_18",
                "prior_slices:17_18_package_exists",
                "present",
                "absent",
            )
        )

    expected_17_20 = monorepo / EXPECTED_17_20_PACKAGE
    exists_17_20 = expected_17_20.is_dir()
    checks.append(
        check(
            "prior_slices:17_20_package_exists",
            exists_17_20,
            EXPECTED_17_20_PACKAGE,
            "prior_slices",
        )
    )
    if not exists_17_20:
        defects.append(
            hard_defect(
                "missing_17_20",
                "prior_slices:17_20_package_exists",
                "present",
                "absent",
            )
        )

    started_17_21 = any((monorepo / cand).exists() for cand in SLICE_17_21_PACKAGE_CANDIDATES)
    checks.append(
        check(
            "prior_slices:17_21_not_started",
            not started_17_21,
            "no 17.21 packages",
            "prior_slices",
        )
    )
    if started_17_21:
        defects.append(
            hard_defect(
                "slice_17_21_started",
                "prior_slices:17_21_not_started",
                "absent",
                "present",
            )
        )

    # Full 22 corpus not re-run: no new suite execution flag under sv17-19.
    corpus_flag = monorepo / ".codestrata-artifacts/validation/suites/sv17-19/full-22-corpus-executed.flag"
    suite_progress = monorepo / ".codestrata-artifacts/validation/suites/sv17-13/progress.jsonl"
    no_new_full_corpus = not corpus_flag.exists()
    checks.append(
        check(
            "prior_slices:no_full_22_rerun",
            no_new_full_corpus,
            "no sv17-19 full-22 flag",
            "prior_slices",
        )
    )
    limitations.append("bounded_representative_subset")

    status_pkgs = (
        monorepo / "verification/community_website_status",
        monorepo / "verification/community_status_api",
        monorepo / "verification/community_vscode_publish",
    )
    no_status = not any(p.exists() for p in status_pkgs)
    checks.append(
        check(
            "prior_slices:community_status_not_implemented",
            no_status,
            "community status deferred",
            "prior_slices",
        )
    )
    if not no_status:
        defects.append(
            hard_defect(
                "status_started",
                "prior_slices:community_status_not_implemented",
                "absent",
                "present",
            )
        )

    summary = {
        "slice_17_18_present": exists_17_18,
        "slice_17_20_present": exists_17_20,
        "slice_17_21_started": started_17_21,
        "full_22_rerun": not no_new_full_corpus,
        "community_status_deferred": no_status,
        "historical_sv17_13_progress_present": suite_progress.is_file(),
    }
    return checks, defects, summary, limitations
