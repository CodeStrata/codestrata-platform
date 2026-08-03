"""Application-layer canonical assessment dataset ingestion (Platform-only).

Dataset ingestion preserves canonical Engine assessment identities and
relationships. It does not rerun analysis, infer missing relationships, or
create portfolio conclusions.
"""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.contracts import (
    AssessmentComparability,
    AssessmentDatasetInput,
    DatasetIngestionResult,
    IntelligenceDatasetSelectionPolicy,
    NormalizedAssessmentSnapshot,
    WebsiteExportEligibility,
)
from codestrata_platform.intelligence_reporting.application.ingestion import (
    ingest_assessment_dataset,
)

__all__ = [
    "AssessmentComparability",
    "AssessmentDatasetInput",
    "DatasetIngestionResult",
    "IntelligenceDatasetSelectionPolicy",
    "NormalizedAssessmentSnapshot",
    "WebsiteExportEligibility",
    "ingest_assessment_dataset",
]
