"""Technology Distribution insights (Platform-only).

Technology distributions describe only the repositories with eligible Technology
Inventory evidence in the selected dataset. They do not establish industry
popularity, technology quality, support status, or modernization need.
"""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.technology_distribution.builder import (
    build_technology_distribution,
    populate_report_technology_distribution,
)
from codestrata_platform.intelligence_reporting.application.technology_distribution.diagnostics import (
    TechnologyDistributionDiagnostics,
    TechnologyDistributionPolicy,
    TechnologyDistributionResult,
)
from codestrata_platform.intelligence_reporting.application.technology_distribution.normalization import (
    NORMALIZATION_POLICY_VERSION,
    normalize_technology_name,
    technology_id,
)

__all__ = [
    "NORMALIZATION_POLICY_VERSION",
    "TechnologyDistributionDiagnostics",
    "TechnologyDistributionPolicy",
    "TechnologyDistributionResult",
    "build_technology_distribution",
    "normalize_technology_name",
    "populate_report_technology_distribution",
    "technology_id",
]
