"""DAU/MAU activity semantics."""

from __future__ import annotations

from typing import Any

from verification.community_insights_event_coverage.schemas import (
    ACTIVATION_NOT_USAGE,
    ACTIVITY_OPERATIONS_USAGE,
)


def activity_rules() -> dict[str, Any]:
    return {
        "do_not_count_every_raw_event": True,
        "usage_operations": sorted(ACTIVITY_OPERATIONS_USAGE),
        "activate_not_usage": ACTIVATION_NOT_USAGE,
        "primary_streams": [
            "assessment_metadata",
            "telemetry",
            "cli_event",
            "extension_event",
            "ai_usage",
        ],
    }
