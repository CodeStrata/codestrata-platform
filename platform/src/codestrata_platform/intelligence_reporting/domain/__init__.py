"""Domain models for commercial Engineering Intelligence Reports."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.domain.capability import (
    AssessmentHeadDistribution,
    CapabilityComparison,
    CapabilityDistribution,
    RepositoryCapabilitySnapshot,
)
from codestrata_platform.intelligence_reporting.domain.confidence import (
    IntelligenceReportConfidence,
)
from codestrata_platform.intelligence_reporting.domain.dataset import (
    IntelligenceDataset,
    RepositoryAssessmentReference,
)
from codestrata_platform.intelligence_reporting.domain.drilldown import (
    RepositoryIntelligenceDrilldown,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ComparabilityStatus,
    ConfidenceLevel,
    DataVisibility,
    DerivationStatus,
    ExclusionReason,
    InclusionStatus,
    LimitationCategory,
    LimitationSeverity,
    ModernizationObservationCategory,
    PatternType,
    ReportScope,
    SourceType,
)
from codestrata_platform.intelligence_reporting.domain.identifiers import (
    DatasetId,
    EngineeringIntelligenceReportId,
    ObservationId,
    PatternId,
    build_dataset_id,
    build_observation_id,
    build_pattern_id,
    build_report_id,
)
from codestrata_platform.intelligence_reporting.domain.limitations import (
    DatasetLimitation,
)
from codestrata_platform.intelligence_reporting.domain.modernization import (
    ModernizationObservation,
)
from codestrata_platform.intelligence_reporting.domain.patterns import (
    RecurringIntelligencePattern,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    ENGINEERING_INTELLIGENCE_REPORT_POLICY_VERSION,
    ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION,
    EngineeringIntelligenceReport,
    GeneratedArtifactMetadata,
    MethodologyNotes,
    ReportExecutiveSummary,
)
from codestrata_platform.intelligence_reporting.domain.repository_snapshot import (
    RepositoryPopulation,
)
from codestrata_platform.intelligence_reporting.domain.technology import (
    Ratio,
    TechnologyCategoryDistribution,
    TechnologyDistribution,
    TechnologyDistributionObservation,
)
from codestrata_platform.intelligence_reporting.domain.visibility import (
    WebsiteExportPolicy,
    WebsiteSafeIntelligenceReport,
)

__all__ = [
    "ENGINEERING_INTELLIGENCE_REPORT_POLICY_VERSION",
    "ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION",
    "AssessmentHeadDistribution",
    "CapabilityComparison",
    "CapabilityDistribution",
    "ComparabilityStatus",
    "ConfidenceLevel",
    "DataVisibility",
    "DatasetId",
    "DatasetLimitation",
    "DerivationStatus",
    "EngineeringIntelligenceReport",
    "EngineeringIntelligenceReportId",
    "ExclusionReason",
    "GeneratedArtifactMetadata",
    "InclusionStatus",
    "IntelligenceDataset",
    "IntelligenceReportConfidence",
    "LimitationCategory",
    "LimitationSeverity",
    "MethodologyNotes",
    "ModernizationObservation",
    "ModernizationObservationCategory",
    "ObservationId",
    "PatternId",
    "PatternType",
    "Ratio",
    "RecurringIntelligencePattern",
    "ReportExecutiveSummary",
    "ReportScope",
    "RepositoryAssessmentReference",
    "RepositoryCapabilitySnapshot",
    "RepositoryIntelligenceDrilldown",
    "RepositoryPopulation",
    "SourceType",
    "TechnologyCategoryDistribution",
    "TechnologyDistribution",
    "TechnologyDistributionObservation",
    "WebsiteExportPolicy",
    "WebsiteSafeIntelligenceReport",
    "build_dataset_id",
    "build_observation_id",
    "build_pattern_id",
    "build_report_id",
]
