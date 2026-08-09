"""Security boundary checks for Slice 17.10."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_cloud_production_recovery.helpers import add_check
from verification.community_cloud_production_recovery.models import CheckResult, Defect


def check_security(
    monorepo: Path, policy: dict[str, Any]
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(
        checks,
        defects,
        "security:no_publish",
        policy.get("publish_allowed") is False and policy.get("tag_allowed") is False,
        "false",
        "security",
    )
    add_check(
        checks,
        defects,
        "security:no_commit_required",
        policy.get("commit_required") is False,
        "false",
        "security",
    )
    add_check(
        checks,
        defects,
        "security:no_redesign",
        policy.get("redesign_infrastructure_allowed") is False,
        "false",
        "security",
    )
    add_check(
        checks,
        defects,
        "security:no_ingestion_modify",
        policy.get("modify_ingestion_allowed") is False,
        "false",
        "security",
    )
    add_check(
        checks,
        defects,
        "security:region",
        policy.get("region") == "us-west-2",
        str(policy.get("region")),
        "security",
    )
    add_check(
        checks,
        defects,
        "security:environment",
        policy.get("environment") == "production",
        str(policy.get("environment")),
        "security",
    )
    summary = {
        "no_publish": True,
        "no_redesign": True,
        "region": policy.get("region"),
        "environment": policy.get("environment"),
    }
    return checks, defects, summary
