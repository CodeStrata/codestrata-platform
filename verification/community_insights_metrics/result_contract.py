"""MetricResult contract freezes."""

from __future__ import annotations

UI_DOES_NOT_COMPUTE = True
AGGREGATION_OWNS_COMPUTATION = True
FORBIDDEN_RESULT_FIELDS = (
    "raw_events",
    "installation_ids",
    "object_keys",
    "payloads",
)
