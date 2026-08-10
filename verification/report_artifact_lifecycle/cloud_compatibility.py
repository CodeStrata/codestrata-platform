"""Cloud compatibility checks for Slice 17.15."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.report_artifact_lifecycle.helpers import add_check
from verification.report_artifact_lifecycle.models import CheckResult, Defect


def check_cloud_compatibility(
    monorepo: Path, policy: dict[str, Any]
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"cloud_deferred": True}

    add_check(
        checks,
        defects,
        "cloud:future_same_retention",
        policy.get("future_cloud_reports_same_retention") is True,
        str(policy.get("future_cloud_reports_same_retention")),
        "cloud_compatibility",
    )

    cloud_modules = (
        "platform/src/codestrata_platform/community_cloud_api/deployment/wiring.py",
        "engine/src/codestrata/community_cloud/public_api_authority.py",
    )
    wired = any((monorepo / rel).is_file() for rel in cloud_modules)
    summary["cloud_deferred"] = not wired or policy.get("future_cloud_reports_same_retention") is True
    add_check(
        checks,
        defects,
        "cloud:deferred",
        summary["cloud_deferred"],
        "cloud report lifecycle deferred; policy declares future parity",
        "cloud_compatibility",
        soft=True,
    )

    return checks, defects, summary
