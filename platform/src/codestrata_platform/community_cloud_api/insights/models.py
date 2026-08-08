"""MetricResult and request models — aggregate-only, no installation IDs/keys."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Literal

Completeness = Literal["complete", "partial", "unavailable", "not_applicable"]
MetricStatus = Literal["ok", "suppressed", "error"]


@dataclass(frozen=True, slots=True)
class MetricWindow:
    start_date_utc: date
    end_date_utc: date
    horizon: str

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "end_date_utc": self.end_date_utc.isoformat(),
            "horizon": self.horizon,
            "start_date_utc": self.start_date_utc.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class MetricGroup:
    dimension: str
    key: str
    count: int
    share: float | None = None
    suppressed: bool = False

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "dimension": self.dimension,
            "key": self.key,
            "share": self.share,
            "suppressed": self.suppressed,
        }


@dataclass(frozen=True, slots=True)
class MetricResult:
    metric_id: str
    status: MetricStatus
    window: MetricWindow
    value: int | float | None
    groups: tuple[MetricGroup, ...] = ()
    completeness: Completeness = "complete"
    denominator: int | float | None = None
    share: float | None = None
    limitations: tuple[str, ...] = ()

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "completeness": self.completeness,
            "denominator": self.denominator,
            "groups": [g.to_stable_dict() for g in self.groups],
            "limitations": list(self.limitations),
            "metric_id": self.metric_id,
            "share": self.share,
            "status": self.status,
            "value": self.value,
            "window": self.window.to_stable_dict(),
        }


@dataclass(frozen=True, slots=True)
class MetricRequest:
    metric_id: str
    start_date_utc: date
    end_date_utc: date


@dataclass(frozen=True, slots=True)
class OverviewRequest:
    start_date_utc: date
    end_date_utc: date
    metric_ids: tuple[str, ...] | None = None


@dataclass
class ReadDiagnostics:
    """Internal usage counters — never include keys or installation IDs."""

    objects_considered: int = 0
    bytes_read: int = 0
    pages_read: int = 0
    get_requests: int = 0
    list_requests: int = 0
    malformed_objects: int = 0
    unsupported_schema_objects: int = 0
    budget_reached: bool = False

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "budget_reached": self.budget_reached,
            "bytes_read": self.bytes_read,
            "get_requests": self.get_requests,
            "list_requests": self.list_requests,
            "malformed_objects": self.malformed_objects,
            "objects_considered": self.objects_considered,
            "pages_read": self.pages_read,
            "unsupported_schema_objects": self.unsupported_schema_objects,
        }


@dataclass
class AggregationContext:
    """In-memory aggregation inputs shared across metrics in a batch."""

    events: list[dict[str, Any]] = field(default_factory=list)
    diagnostics: ReadDiagnostics = field(default_factory=ReadDiagnostics)
    missing_installation_id_count: int = 0
