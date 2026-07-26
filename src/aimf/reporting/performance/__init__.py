"""Performance Intelligence report presentation (Phase 4.9.6)."""

from aimf.reporting.performance.adapter import PerformanceReportAdapter
from aimf.reporting.performance.models import (
    PERFORMANCE_REPORT_SECTION_ID,
    PERFORMANCE_REPORT_SECTION_VERSION,
    PerformanceReportSection,
)

__all__ = [
    "PERFORMANCE_REPORT_SECTION_ID",
    "PERFORMANCE_REPORT_SECTION_VERSION",
    "PerformanceReportAdapter",
    "PerformanceReportSection",
]
