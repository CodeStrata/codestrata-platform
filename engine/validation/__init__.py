"""Multi-repository assessment validation harness (Epic 4 Slice 4.1).

Infrastructure only. Does not embed assumptions about any one repository.
Pack-specific accuracy validators and the initial 5–7 repository set belong
to later slices.
"""

from __future__ import annotations

from validation.architecture import (
    AggregateArchitectureMetrics,
    ArchitectureExpectation,
    ArchitectureValidationResult,
    aggregate_architecture_results,
    validate_architecture_precision,
)
from validation.compare import ComparisonMismatch, compare_actual_to_expected
from validation.inventory import (
    AggregateInventoryMetrics,
    FactClassification,
    InventoryValidationResult,
    TechnologyInventoryExpectation,
    aggregate_inventory_results,
    validate_technology_inventory,
)
from validation.models import (
    ActualAssessmentResult,
    ComparisonOutcome,
    ExpectedResults,
    PackPrecisionRecord,
    ValidationRepository,
    ValidationRunResult,
    ValidationSummary,
    ValidationVerdict,
)
from validation.security import (
    AggregateSecurityMetrics,
    SecurityExpectation,
    SecurityValidationResult,
    aggregate_security_results,
    validate_security_precision,
)
from validation.summary import build_validation_summary
from validation.technical_debt import (
    AggregateTechnicalDebtMetrics,
    TechnicalDebtExpectation,
    TechnicalDebtValidationResult,
    aggregate_technical_debt_results,
    validate_technical_debt_precision,
)
from validation.dependency import (
    AggregateDependencyMetrics,
    DependencyExpectation,
    DependencyValidationResult,
    aggregate_dependency_results,
    validate_dependency_precision,
)
from validation.cloud import (
    AggregateCloudMetrics,
    CloudExpectation,
    CloudValidationResult,
    aggregate_cloud_results,
    validate_cloud_precision,
)
from validation.ai_readiness import (
    AggregateAiReadinessMetrics,
    AiReadinessExpectation,
    AiReadinessValidationResult,
    aggregate_ai_readiness_results,
    validate_ai_readiness_precision,
)
from validation.modernization import (
    AggregateModernizationMetrics,
    ModernizationExpectation,
    ModernizationValidationResult,
    aggregate_modernization_results,
    validate_modernization_precision,
)
from validation.recording import (
    RepositoryValidationRecord,
    load_repository_validation_record,
    write_repository_validation_record,
)
from validation.summary_artifact import (
    OverallVerdict,
    SUMMARY_SCHEMA_VERSION,
    ValidationSummaryArtifact,
)
from validation.summary_from_records import (
    generate_summary_from_records,
    build_summary_artifact,
)

__all__ = [
    "ActualAssessmentResult",
    "AggregateArchitectureMetrics",
    "AggregateInventoryMetrics",
    "AggregateSecurityMetrics",
    "AggregateTechnicalDebtMetrics",
    "AggregateAiReadinessMetrics",
    "AggregateCloudMetrics",
    "AggregateDependencyMetrics",
    "AggregateModernizationMetrics",
    "AiReadinessExpectation",
    "AiReadinessValidationResult",
    "ArchitectureExpectation",
    "ArchitectureValidationResult",
    "CloudExpectation",
    "CloudValidationResult",
    "ComparisonMismatch",
    "ComparisonOutcome",
    "DependencyExpectation",
    "DependencyValidationResult",
    "ExpectedResults",
    "FactClassification",
    "InventoryValidationResult",
    "ModernizationExpectation",
    "ModernizationValidationResult",
    "OverallVerdict",
    "PackPrecisionRecord",
    "RepositoryValidationRecord",
    "SUMMARY_SCHEMA_VERSION",
    "SecurityExpectation",
    "SecurityValidationResult",
    "TechnicalDebtExpectation",
    "TechnicalDebtValidationResult",
    "TechnologyInventoryExpectation",
    "ValidationRepository",
    "ValidationRunResult",
    "ValidationSummary",
    "ValidationSummaryArtifact",
    "ValidationVerdict",
    "aggregate_ai_readiness_results",
    "aggregate_architecture_results",
    "aggregate_cloud_results",
    "aggregate_dependency_results",
    "aggregate_inventory_results",
    "aggregate_modernization_results",
    "aggregate_security_results",
    "aggregate_technical_debt_results",
    "build_summary_artifact",
    "build_validation_summary",
    "compare_actual_to_expected",
    "generate_summary_from_records",
    "load_repository_validation_record",
    "validate_ai_readiness_precision",
    "validate_architecture_precision",
    "validate_cloud_precision",
    "validate_dependency_precision",
    "validate_modernization_precision",
    "validate_security_precision",
    "validate_technical_debt_precision",
    "validate_technology_inventory",
    "write_repository_validation_record",
]
