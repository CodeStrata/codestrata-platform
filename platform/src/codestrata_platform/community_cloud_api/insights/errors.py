"""Aggregation errors — no boto/raw storage details."""

from __future__ import annotations


class InsightsAggregationError(Exception):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(code if not detail else f"{code}:{detail}")


INVALID_METRIC = "invalid_metric"
INVALID_WINDOW = "invalid_window"
STORAGE_UNAVAILABLE = "storage_unavailable"
QUERY_LIMIT_EXCEEDED = "query_limit_exceeded"
UNSUPPORTED_SCHEMA = "unsupported_schema"
MALFORMED_DATA = "malformed_data"
EXTERNAL_SOURCE_UNAVAILABLE = "external_source_unavailable"
INTERNAL_AGGREGATION_ERROR = "internal_aggregation_error"

BOUNDED_ERROR_CODES: frozenset[str] = frozenset(
    {
        INVALID_METRIC,
        INVALID_WINDOW,
        STORAGE_UNAVAILABLE,
        QUERY_LIMIT_EXCEEDED,
        UNSUPPORTED_SCHEMA,
        MALFORMED_DATA,
        EXTERNAL_SOURCE_UNAVAILABLE,
        INTERNAL_AGGREGATION_ERROR,
    }
)
