"""Commercial Engineering Intelligence Report package (Platform-only).

Cross-repository intelligence reporting. Community Engine must not import this
package. Aggregation and rendering are out of scope for Slice 6.1.
"""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.domain.report import (
    ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION,
    EngineeringIntelligenceReport,
)

__all__ = [
    "ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION",
    "EngineeringIntelligenceReport",
]
