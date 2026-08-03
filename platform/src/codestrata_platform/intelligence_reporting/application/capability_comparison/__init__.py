"""Capability and assessment-head comparison (Platform-only).

Capability comparisons describe the assessed repository/head states within the
selected dataset. They do not rank repositories, measure engineering-team
performance, or establish organizational maturity.
"""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.capability_comparison.builder import (
    build_capability_comparisons,
    populate_report_capability_comparisons,
)
from codestrata_platform.intelligence_reporting.application.capability_comparison.head_catalog import (
    COMMERCIAL_HEAD_CATALOG,
    canonicalize_assessment_head,
)
from codestrata_platform.intelligence_reporting.application.capability_comparison.policy import (
    CapabilityComparisonDiagnostics,
    CapabilityComparisonPolicy,
    CapabilityComparisonResult,
    PriorityActionOwnershipPolicy,
)

__all__ = [
    "COMMERCIAL_HEAD_CATALOG",
    "CapabilityComparisonDiagnostics",
    "CapabilityComparisonPolicy",
    "CapabilityComparisonResult",
    "PriorityActionOwnershipPolicy",
    "build_capability_comparisons",
    "canonicalize_assessment_head",
    "populate_report_capability_comparisons",
]
