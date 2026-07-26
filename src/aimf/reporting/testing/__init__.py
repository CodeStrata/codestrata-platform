"""Test report presentation package (Phase 4.6.6)."""

from aimf.reporting.testing.adapter import TestingReportAdapter
from aimf.reporting.testing.models import (
    TESTING_REPORT_SECTION_ID,
    TESTING_REPORT_SECTION_VERSION,
    TestingReportSection,
)

__all__ = [
    "TESTING_REPORT_SECTION_ID",
    "TESTING_REPORT_SECTION_VERSION",
    "TestingReportAdapter",
    "TestingReportSection",
]
