"""Query plan models — no AWS types."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True, slots=True)
class QueryBudgets:
    max_keys_per_page: int = 1000
    max_pages_per_query: int = 20
    # Worst case day prefixes: MAX_DATE_SPAN_DAYS_LIFETIME (365) × 5 streams × 1 schema.
    # Prior default (50) was below a normal 31-day × multi-stream overview plan (~155 lists),
    # which forced query_budget_reached with almost no objects present.
    max_list_requests_per_query: int = 2000
    max_get_requests_per_query: int = 2000
    max_objects_per_query: int = 2000
    max_bytes_per_query: int = 100_000_000
    max_single_object_bytes: int = 70_000

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "max_bytes_per_query": self.max_bytes_per_query,
            "max_get_requests_per_query": self.max_get_requests_per_query,
            "max_keys_per_page": self.max_keys_per_page,
            "max_list_requests_per_query": self.max_list_requests_per_query,
            "max_objects_per_query": self.max_objects_per_query,
            "max_pages_per_query": self.max_pages_per_query,
            "max_single_object_bytes": self.max_single_object_bytes,
        }


@dataclass(frozen=True, slots=True)
class DateWindow:
    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        if self.end_date < self.start_date:
            raise ValueError("end_before_start")


@dataclass(frozen=True, slots=True)
class QueryPlan:
    streams: tuple[str, ...]
    schema_versions: tuple[str, ...]
    prefixes: tuple[str, ...]
    start_date: str
    end_date: str
    budgets: QueryBudgets
    quarantine_excluded: bool = True
    completeness_default: str = "complete"
    metric: str | None = None

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "budgets": self.budgets.to_stable_dict(),
            "completeness_default": self.completeness_default,
            "end_date": self.end_date,
            "metric": self.metric,
            "prefixes": list(self.prefixes),
            "quarantine_excluded": self.quarantine_excluded,
            "schema_versions": list(self.schema_versions),
            "start_date": self.start_date,
            "streams": list(self.streams),
        }
