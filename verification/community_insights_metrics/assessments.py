"""Assessment success/failure/cancelled freezes."""

from __future__ import annotations

CANCELLED_NOT_FAILED = True
CANCELLED_EXCLUDED = True
SUCCESS_STATUSES = frozenset(
    {"completed", "partially_completed", "succeeded", "partially_succeeded"}
)
FAILED_STATUSES = frozenset({"failed"})
NOT_FAILURE_CAUSES = frozenset(
    {
        "report_missing",
        "report_open_failure",
        "telemetry_failure",
        "analytics_failure",
    }
)
