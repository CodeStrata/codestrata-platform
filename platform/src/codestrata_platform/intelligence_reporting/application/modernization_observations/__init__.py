"""Evidence-backed portfolio modernization observations (Platform-only).

Modernization observations summarize repeated deterministic repository-level
actions within the selected assessed dataset. They are not portfolio
Recommendations, delivery commitments, ROI claims, or transformation plans.
"""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.modernization_observations.builder import (
    build_modernization_observations,
    populate_report_modernization_observations,
)
from codestrata_platform.intelligence_reporting.application.modernization_observations.policy import (
    ACTION_IDENTITY_CATALOG_VERSION,
    STATEMENT_TEMPLATE_VERSION,
    ModernizationObservationDiagnostics,
    ModernizationObservationPolicy,
    ModernizationObservationResult,
)

__all__ = [
    "ACTION_IDENTITY_CATALOG_VERSION",
    "STATEMENT_TEMPLATE_VERSION",
    "ModernizationObservationDiagnostics",
    "ModernizationObservationPolicy",
    "ModernizationObservationResult",
    "build_modernization_observations",
    "populate_report_modernization_observations",
]
