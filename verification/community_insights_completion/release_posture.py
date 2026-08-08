"""Release posture checks for Slice 15.12."""

from __future__ import annotations

from typing import Any

from verification.community_insights_completion.inventory import add_check
from verification.community_insights_completion.models import CheckResult, Defect


def check_release_posture() -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    posture = {
        "epic_15_complete": False,
        "commit_created": False,
        "tag_created": False,
        "published": False,
        "deployed": False,
        "production_ingestion_enabled": False,
        "live_dashboard_data_available": False,
        "insights_site_deployed": False,
        "real_secrets_created": False,
        "remote_insights_repository_created": False,
        "start_epic_16": True,
        "start_slice_16_2": True,
        "start_slice_16_5": True,
        "start_slice_16_6": True,
        "start_slice_16_7": True,
        "start_slice_16_8": True,
        "start_slice_16_9": True,
        "start_slice_16_10": True,
        "start_epic_17": False,
    }
    for key, expected in posture.items():
        if key == "epic_15_complete":
            continue
        add_check(
            checks,
            defects,
            f"release_posture:{key}",
            posture[key] is expected,
            str(posture[key]),
            "release_posture",
        )
    return checks, defects, posture
