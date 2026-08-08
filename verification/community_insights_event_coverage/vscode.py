"""VS Code usage coverage helpers."""

from __future__ import annotations

from typing import Any

from verification.community_insights_event_coverage.schemas import (
    ACTIVATION_NOT_USAGE,
    ACTIVITY_OPERATIONS_USAGE,
)


def vscode_rules() -> dict[str, Any]:
    return {
        "stream": "extension_event",
        "usage_operations": sorted(ACTIVITY_OPERATIONS_USAGE),
        "activate_alone_counts_as_usage": False,
        "activation_operation": ACTIVATION_NOT_USAGE,
        "version_field": "payload.client.version",
    }
