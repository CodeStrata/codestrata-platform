"""Stable vocabularies for commercial intelligence reporting."""

from __future__ import annotations

from enum import StrEnum


class ReportScope(StrEnum):
    PUBLIC_OSS_DATASET = "public_oss_dataset"
    CUSTOMER_WORKSPACE = "customer_workspace"
    CUSTOMER_PORTFOLIO = "customer_portfolio"
    DESIGN_PARTNER_DATASET = "design_partner_dataset"
    INTERNAL_VALIDATION_DATASET = "internal_validation_dataset"
    OTHER = "other"


class SourceType(StrEnum):
    LOCAL = "local"
    REMOTE = "remote"
    PUBLIC_OSS = "public_oss"
    PRIVATE = "private"
    CUSTOMER_PRIVATE = "customer_private"
    INTERNAL_VALIDATION = "internal_validation"
    DESIGN_PARTNER = "design_partner"
    IMPORTED_ARTIFACT = "imported_artifact"
    FIXTURE = "fixture"
    OTHER = "other"


class InclusionStatus(StrEnum):
    INCLUDED = "included"
    EXCLUDED = "excluded"
    PARTIAL = "partial"
    REJECTED = "rejected"
    LEGACY_LIMITED = "legacy_limited"
    UNAVAILABLE = "unavailable"


class ExclusionReason(StrEnum):
    DUPLICATE_REPOSITORY = "duplicate_repository"
    SUPERSEDED_ASSESSMENT = "superseded_assessment"
    UNSUPPORTED_SCHEMA = "unsupported_schema"
    MALFORMED_REPORT = "malformed_report"
    TRACEABILITY_FAILURE = "traceability_failure"
    VISIBILITY_RESTRICTION = "visibility_restriction"
    MISSING_REVISION = "missing_revision"
    INCOMPLETE_IDENTITY = "incomplete_identity"
    EXPLICITLY_EXCLUDED = "explicitly_excluded"
    NOT_COMPARABLE = "not_comparable"
    DUPLICATE_CONFLICT = "duplicate_conflict"
    AMBIGUOUS_RUN_SELECTION = "ambiguous_run_selection"
    UNSAFE_METADATA = "unsafe_metadata"
    OTHER = "other"


class ComparabilityStatus(StrEnum):
    COMPARABLE = "comparable"
    PARTIALLY_COMPARABLE = "partially_comparable"
    NOT_COMPARABLE = "not_comparable"
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"


class ConfidenceLevel(StrEnum):
    HIGH = "high"
    MODERATE = "moderate"
    LIMITED = "limited"
    UNAVAILABLE = "unavailable"


class DerivationStatus(StrEnum):
    DERIVED = "derived"
    PROVISIONAL = "provisional"
    UNAVAILABLE = "unavailable"
    DEFERRED = "deferred"


class DataVisibility(StrEnum):
    PUBLIC = "public"
    CUSTOMER_PRIVATE = "customer_private"
    INTERNAL = "internal"
    ANONYMIZED = "anonymized"


class PatternType(StrEnum):
    RECURRING_FINDING = "recurring_finding"
    RECURRING_RULE = "recurring_rule"
    RECURRING_CONFIGURATION_CONDITION = "recurring_configuration_condition"
    RECURRING_DEPENDENCY_CONDITION = "recurring_dependency_condition"
    RECURRING_ARCHITECTURE_CONDITION = "recurring_architecture_condition"
    RECURRING_COMPLEXITY_CONDITION = "recurring_complexity_condition"
    RECURRING_TECHNOLOGY_CONDITION = "recurring_technology_condition"
    RECURRING_RECOMMENDATION = "recurring_recommendation"
    RECURRING_PRIORITY_ACTION = "recurring_priority_action"
    OTHER = "other"


class ModernizationObservationCategory(StrEnum):
    SHARED_FOUNDATION = "shared_foundation"
    SECURITY_REMEDIATION = "security_remediation"
    DEPENDENCY_GOVERNANCE = "dependency_governance"
    ARCHITECTURE_MODERNIZATION = "architecture_modernization"
    MAINTAINABILITY = "maintainability"
    TESTING_ENABLEMENT = "testing_enablement"
    CLOUD_ENABLEMENT = "cloud_enablement"
    AI_ENABLEMENT = "ai_enablement"
    OPERATIONAL_READINESS = "operational_readiness"
    OTHER = "other"


class LimitationCategory(StrEnum):
    SELECTION_BIAS = "selection_bias"
    SAMPLE_SIZE = "sample_size"
    LANGUAGE_REPRESENTATION = "language_representation"
    ECOSYSTEM_REPRESENTATION = "ecosystem_representation"
    REPOSITORY_SIZE_REPRESENTATION = "repository_size_representation"
    CONTROLLED_FIXTURE_PRESENCE = "controlled_fixture_presence"
    ASSESSMENT_COVERAGE = "assessment_coverage"
    ASSESSMENT_CONFIDENCE = "assessment_confidence"
    UNSUPPORTED_CAPABILITY = "unsupported_capability"
    SCHEMA_COMPATIBILITY = "schema_compatibility"
    METHODOLOGY_COMPATIBILITY = "methodology_compatibility"
    ASSESSMENT_AGE = "assessment_age"
    MISSING_REVISION = "missing_revision"
    NON_TEMPORAL_DATASET = "non_temporal_dataset"
    SOURCE_VISIBILITY = "source_visibility"
    INCOMPLETE_TRACEABILITY = "incomplete_traceability"
    DENOMINATOR_AVAILABILITY = "denominator_availability"
    SECTION_SUPPORT = "section_support"
    LEGACY_SOURCE = "legacy_source"
    OTHER = "other"


class LimitationSeverity(StrEnum):
    """Interpretation impact — not Finding Severity."""

    MATERIAL = "material"
    MODERATE = "moderate"
    MINOR = "minor"
    INFORMATIONAL = "informational"


class ActivationStatus(StrEnum):
    ACTIVATED = "activated"
    AVAILABLE = "available"
    DISABLED = "disabled"
    UNAVAILABLE = "unavailable"


class CoverageStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"


class VersionState(StrEnum):
    KNOWN = "known"
    UNAVAILABLE = "unavailable"
    CONFLICTING = "conflicting"


class RatioStatus(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
