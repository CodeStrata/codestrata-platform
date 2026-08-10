"""Docs distinguish Data Lake vs Report Artifact Store."""

from __future__ import annotations

from pathlib import Path

from verification.community_data_lake_insights.contract import (
    DOCS_COMMUNITY_API,
    DOCS_PRIVACY,
)
from verification.community_data_lake_insights.helpers import check, read_text
from verification.community_data_lake_insights.models import CheckResult, Defect


def check_docs(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    privacy = read_text(monorepo / DOCS_PRIVACY)
    api = read_text(monorepo / DOCS_COMMUNITY_API)
    combined = privacy + "\n" + api
    lower = combined.lower()

    distinguishes = (
        "data lake" in lower
        and ("report artifact" in lower or "report artifacts" in lower)
    )
    checks.append(
        check(
            "docs:distinguishes_lake_vs_report_store",
            distinguishes,
            "privacy + community-api distinguish stores",
            "docs",
        )
    )
    if not distinguishes:
        defects.append(
            Defect(
                "docs_boundary",
                "docs:distinguishes_lake_vs_report_store",
                "both named",
                "missing",
            )
        )

    # Narrow defect: claims reports stored in data lake
    claims_reports_in_lake = (
        "reports are stored in" in lower
        and "data lake" in lower
        and "not the community data lake" not in lower
        and "not the data lake" not in lower
    )
    # More precise: look for dangerous phrasing
    dangerous = False
    for line in combined.splitlines():
        ll = line.lower()
        if "data lake" in ll and "report" in ll:
            if any(
                phrase in ll
                for phrase in (
                    "not the community data lake",
                    "not the data lake",
                    "not in the data lake",
                    "not the community",
                )
            ):
                continue
            if any(
                phrase in ll
                for phrase in (
                    "stored in the data lake",
                    "stored in data lake",
                    "reports in the data lake",
                    "report artifacts in the data lake",
                )
            ):
                dangerous = True
    checks.append(
        check(
            "docs:no_reports_claimed_in_data_lake",
            not dangerous and not claims_reports_in_lake,
            "docs do not claim reports live in data lake",
            "docs",
        )
    )
    if dangerous or claims_reports_in_lake:
        defects.append(
            Defect(
                "docs_reports_in_lake",
                "docs:no_reports_claimed_in_data_lake",
                "absent claim",
                "docs claim reports in data lake",
            )
        )

    summary = {
        "privacy_page": True,
        "community_api_page": True,
        "distinguishes_stores": distinguishes,
        "reports_claimed_in_data_lake": dangerous or claims_reports_in_lake,
    }
    return checks, defects, summary
