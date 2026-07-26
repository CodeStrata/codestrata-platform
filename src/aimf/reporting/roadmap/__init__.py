"""Roadmap report presentation package (Phase 5.10)."""

from aimf.reporting.roadmap.models import (
    ROADMAP_REPORT_SECTION_ID,
    ROADMAP_REPORT_SECTION_VERSION,
    RoadmapReportSection,
)

__all__ = [
    "ROADMAP_REPORT_SECTION_ID",
    "ROADMAP_REPORT_SECTION_VERSION",
    "RoadmapReportSection",
]


def __getattr__(name: str) -> object:
    if name == "RoadmapReportAdapter":
        from aimf.reporting.roadmap.adapter import RoadmapReportAdapter

        return RoadmapReportAdapter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
