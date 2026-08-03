"""Application contracts for canonical assessment dataset ingestion."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from codestrata_platform.intelligence_reporting.domain.dataset import IntelligenceDataset
from codestrata_platform.intelligence_reporting.domain.enums import (
    ComparabilityStatus,
    DataVisibility,
    InclusionStatus,
    SourceType,
)


SUPPORTED_ASSESSMENT_SCHEMA_VERSION = "1.2"
LEGACY_COMPATIBLE_SCHEMA_VERSIONS = frozenset({"1.0", "1.1"})


class AssessmentSelectionMode(StrEnum):
    EXPLICITLY_SELECTED = "explicitly_selected"
    LATEST_SUCCESSFUL = "latest_successful"
    LATEST_COMPARABLE = "latest_comparable"
    PINNED_ASSESSMENT_RUN = "pinned_assessment_run"


class DuplicateRepositoryBehavior(StrEnum):
    FAIL_CLOSED = "fail_closed"
    EXPLICIT_SELECTION_WINS = "explicit_selection_wins"


class FailedAssessmentBehavior(StrEnum):
    CONTINUE_WITH_DIAGNOSTICS = "continue_with_diagnostics"
    FAIL_FAST = "fail_fast"


class SchemaCompatibilityPolicy(StrEnum):
    REQUIRE_1_2_COMPLETE = "require_1_2_complete"
    ALLOW_LEGACY_LIMITED = "allow_legacy_limited"


class IngestionStatus(StrEnum):
    NORMALIZED = "normalized"
    LEGACY_LIMITED = "legacy_limited"
    REJECTED = "rejected"
    EXCLUDED = "excluded"


class DisplayNamePolicy(StrEnum):
    USE_PROVIDED = "use_provided"
    ANONYMIZE = "anonymize"
    OMIT = "omit"


@dataclass(frozen=True, slots=True)
class IntelligenceDatasetSelectionPolicy:
    """Explicit dataset selection policy — prefer explicit assessment-run selection."""

    policy_id: str = "intelligence-dataset-selection"
    policy_version: str = "v1"
    repository_selection: str = "explicit_inputs"
    assessment_selection: AssessmentSelectionMode = AssessmentSelectionMode.EXPLICITLY_SELECTED
    duplicate_repository_behavior: DuplicateRepositoryBehavior = (
        DuplicateRepositoryBehavior.EXPLICIT_SELECTION_WINS
    )
    schema_compatibility_policy: SchemaCompatibilityPolicy = (
        SchemaCompatibilityPolicy.ALLOW_LEGACY_LIMITED
    )
    failed_assessment_behavior: FailedAssessmentBehavior = (
        FailedAssessmentBehavior.CONTINUE_WITH_DIAGNOSTICS
    )
    visibility_policy: str = "explicit_visibility_required"
    source_revision_policy: str = "pinned_revision_preferred"
    # repository_id -> assessment_run_id when multiple runs are supplied
    selected_assessment_runs: Mapping[str, str] = field(default_factory=dict)
    require_pinned_revision_for_public_oss: bool = False

    @property
    def selection_policy_token(self) -> str:
        return f"{self.policy_id}:{self.policy_version}"


@dataclass(frozen=True, slots=True)
class AssessmentDatasetInput:
    """One repository assessment candidate for dataset construction."""

    repository_id: str
    assessment_id: str
    assessment_run_id: str
    report_document: Mapping[str, Any] | None = None
    report_reference: str | None = None
    workspace_id: str | None = None
    organization_id: str | None = None
    source_type: SourceType = SourceType.OTHER
    source_reference: str | None = None
    pinned_revision: str | None = None
    visibility: DataVisibility = DataVisibility.ANONYMIZED
    inclusion_status: InclusionStatus = InclusionStatus.INCLUDED
    dataset_tags: tuple[str, ...] = ()
    display_name: str | None = None
    display_name_policy: DisplayNamePolicy = DisplayNamePolicy.USE_PROVIDED
    source_reference_publication_permitted: bool = False
    limitations: tuple[str, ...] = ()
    explicitly_selected: bool = False


@dataclass(frozen=True, slots=True)
class EntityReference:
    """Safe bounded reference — IDs and labels only, no snippets/bodies."""

    entity_id: str
    entity_kind: str
    assessment_id: str
    repository_id: str
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WebsiteExportEligibility:
    """Precheck only — does not render website export."""

    eligible: bool
    requires_anonymization: bool
    blocking_reasons: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class NormalizedAssessmentSnapshot:
    """Bounded projection of one canonical assessment — not a second SoT."""

    repository_id: str
    assessment_id: str
    assessment_run_id: str
    assessment_schema_version: str
    source_type: SourceType
    visibility: DataVisibility
    inclusion_status: InclusionStatus
    ingestion_status: IngestionStatus
    canonical_report_digest: str
    workspace_id: str | None = None
    organization_id: str | None = None
    assessment_timestamp: str | None = None
    source_reference: str | None = None
    pinned_revision: str | None = None
    display_name: str | None = None
    source_reference_publication_permitted: bool = False
    enabled_assessment_heads: tuple[str, ...] = ()
    available_assessment_heads: tuple[str, ...] = ()
    disabled_assessment_heads: tuple[str, ...] = ()
    unavailable_assessment_heads: tuple[str, ...] = ()
    missing_assessment_heads: tuple[str, ...] = ()
    assessment_head_confidence: Mapping[str, str] = field(default_factory=dict)
    assessment_coverage: Mapping[str, str] = field(default_factory=dict)
    technology_refs: tuple[EntityReference, ...] = ()
    finding_refs: tuple[EntityReference, ...] = ()
    recommendation_refs: tuple[EntityReference, ...] = ()
    priority_action_refs: tuple[EntityReference, ...] = ()
    roadmap_refs: tuple[EntityReference, ...] = ()
    correlation_refs: tuple[EntityReference, ...] = ()
    evidence_refs: tuple[EntityReference, ...] = ()
    canonical_report_reference: str | None = None
    traceability_status: str = "legacy"
    available_canonical_sections: tuple[str, ...] = ()
    website_export_eligibility: WebsiteExportEligibility | None = None
    limitations: tuple[str, ...] = ()
    exclusion_reason: str | None = None
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AssessmentComparability:
    status: ComparabilityStatus
    compatible_repository_ids: tuple[str, ...] = ()
    incompatible_repository_ids: tuple[str, ...] = ()
    schema_versions: tuple[str, ...] = ()
    methodology_versions: tuple[str, ...] = ()
    assessment_head_compatibility: Mapping[str, str] = field(default_factory=dict)
    selection_policy_compatibility: str = "unknown"
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DatasetIngestionDiagnostic:
    code: str
    message: str
    repository_id: str | None = None
    assessment_id: str | None = None
    assessment_run_id: str | None = None


@dataclass(frozen=True, slots=True)
class DatasetIngestionResult:
    dataset: IntelligenceDataset | None
    included: tuple[NormalizedAssessmentSnapshot, ...] = ()
    excluded: tuple[NormalizedAssessmentSnapshot, ...] = ()
    rejected: tuple[NormalizedAssessmentSnapshot, ...] = ()
    comparability: AssessmentComparability | None = None
    diagnostics: tuple[DatasetIngestionDiagnostic, ...] = ()
    selection_policy_token: str = ""
