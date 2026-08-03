"""Explicit application errors for commercial dataset ingestion."""

from __future__ import annotations

from codestrata_platform.application.common.errors import ApplicationError


class IntelligenceReportingIngestionError(ApplicationError):
    """Base error for commercial intelligence dataset ingestion."""


class UnsupportedAssessmentSchemaError(IntelligenceReportingIngestionError):
    """Assessment report schema is unsupported for commercial dataset ingestion."""


class MalformedAssessmentReportError(IntelligenceReportingIngestionError):
    """Assessment report document is malformed or not a JSON object."""


class AssessmentTraceabilityError(IntelligenceReportingIngestionError):
    """Canonical report failed Engine/Platform traceability validation."""


class DuplicateAssessmentConflictError(IntelligenceReportingIngestionError):
    """Same assessment/run ID supplied with conflicting canonical digests."""


class AmbiguousRepositoryAssessmentError(IntelligenceReportingIngestionError):
    """Multiple assessment runs for one repository without explicit selection."""


class UnsafeAssessmentMetadataError(IntelligenceReportingIngestionError):
    """Assessment metadata contains paths, secrets, or other unsafe values."""


class DatasetComparabilityError(IntelligenceReportingIngestionError):
    """Dataset inputs are not comparable under the active selection policy."""


class DatasetInvariantError(IntelligenceReportingIngestionError):
    """Constructed IntelligenceDataset violated domain invariants."""


class IntelligenceReportingAggregationError(ApplicationError):
    """Base error for commercial cross-repository aggregation."""


class AggregationInvariantError(IntelligenceReportingAggregationError):
    """Aggregation facts violated invariants or failed validation."""


class AggregationVisibilityError(IntelligenceReportingAggregationError):
    """Aggregation visibility policy rejected the dataset contents."""


class AggregationUnresolvedReferenceError(IntelligenceReportingAggregationError):
    """Entity support references could not be resolved within the source assessment."""
