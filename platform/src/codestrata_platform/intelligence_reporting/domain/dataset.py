"""Intelligence dataset and repository assessment references."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from codestrata_platform.domain.errors import InvariantViolationError, InvalidValueError
from codestrata_platform.intelligence_reporting.domain._safety import (
    bound_title,
    optional_sorted_ids,
    reject_unsafe_text,
    require_nonblank,
    unique_sorted_ids,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ComparabilityStatus,
    DataVisibility,
    InclusionStatus,
    SourceType,
)
from codestrata_platform.intelligence_reporting.domain.identifiers import (
    DatasetId,
    build_dataset_id,
)
from codestrata_platform.intelligence_reporting.domain.limitations import DatasetLimitation

DATASET_SELECTION_POLICY_VERSION = "intelligence-dataset-selection-v1"


@dataclass(frozen=True, slots=True)
class RepositoryAssessmentReference:
    """Reference to one canonical repository assessment — not a full report embed."""

    repository_id: str
    assessment_id: str
    assessment_run_id: str
    source_type: SourceType
    assessment_schema_version: str
    inclusion_status: InclusionStatus
    visibility: DataVisibility
    workspace_id: str | None = None
    source_reference: str | None = None
    pinned_revision: str | None = None
    assessment_timestamp: str | None = None  # ISO string for display only; not identity
    enabled_assessment_heads: tuple[str, ...] = ()
    available_assessment_heads: tuple[str, ...] = ()
    assessment_coverage_refs: tuple[str, ...] = ()
    assessment_confidence_refs: tuple[str, ...] = ()
    canonical_report_reference: str | None = None
    display_name: str | None = None
    source_reference_publication_permitted: bool = False
    path_exposure_permitted: bool = False
    evidence_exposure_permitted: bool = False
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "repository_id", require_nonblank(self.repository_id, label="repository_id")
        )
        object.__setattr__(
            self, "assessment_id", require_nonblank(self.assessment_id, label="assessment_id")
        )
        object.__setattr__(
            self,
            "assessment_run_id",
            require_nonblank(self.assessment_run_id, label="assessment_run_id"),
        )
        object.__setattr__(
            self,
            "assessment_schema_version",
            require_nonblank(self.assessment_schema_version, label="assessment_schema_version"),
        )
        if self.workspace_id is not None:
            object.__setattr__(
                self, "workspace_id", require_nonblank(self.workspace_id, label="workspace_id")
            )
        if self.source_reference is not None:
            object.__setattr__(
                self,
                "source_reference",
                reject_unsafe_text(self.source_reference, label="source_reference"),
            )
        if self.pinned_revision is not None:
            object.__setattr__(
                self,
                "pinned_revision",
                require_nonblank(self.pinned_revision, label="pinned_revision"),
            )
        if self.canonical_report_reference is not None:
            object.__setattr__(
                self,
                "canonical_report_reference",
                reject_unsafe_text(
                    self.canonical_report_reference, label="canonical_report_reference"
                ),
            )
        if self.display_name is not None:
            object.__setattr__(self, "display_name", bound_title(self.display_name))
        object.__setattr__(
            self,
            "enabled_assessment_heads",
            optional_sorted_ids(self.enabled_assessment_heads, label="enabled_assessment_head"),
        )
        object.__setattr__(
            self,
            "available_assessment_heads",
            optional_sorted_ids(
                self.available_assessment_heads, label="available_assessment_head"
            ),
        )
        object.__setattr__(
            self,
            "assessment_coverage_refs",
            optional_sorted_ids(
                self.assessment_coverage_refs, label="assessment_coverage_ref"
            ),
        )
        object.__setattr__(
            self,
            "assessment_confidence_refs",
            optional_sorted_ids(
                self.assessment_confidence_refs, label="assessment_confidence_ref"
            ),
        )
        object.__setattr__(
            self, "limitations", optional_sorted_ids(self.limitations, label="limitation")
        )
        if (
            self.visibility is DataVisibility.PUBLIC
            and self.source_reference
            and not self.source_reference_publication_permitted
        ):
            raise InvalidValueError(
                "public visibility requires source_reference_publication_permitted",
                reason_code="public_source_publication_not_permitted",
            )

    def identity_material(self) -> dict[str, str]:
        return {
            "repository_id": self.repository_id,
            "assessment_id": self.assessment_id,
            "assessment_run_id": self.assessment_run_id,
            "pinned_revision": self.pinned_revision or "",
            "assessment_schema_version": self.assessment_schema_version,
            "inclusion_status": self.inclusion_status.value,
        }


@dataclass(frozen=True, slots=True)
class ExcludedRepository:
    repository_id: str
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "repository_id", require_nonblank(self.repository_id, label="repository_id")
        )
        object.__setattr__(self, "reason", reject_unsafe_text(self.reason, label="reason"))


@dataclass(frozen=True, slots=True)
class AssessmentTimeRange:
    """Display-only range; never used in identity material."""

    earliest_assessment_timestamp: str | None = None
    latest_assessment_timestamp: str | None = None


@dataclass(frozen=True, slots=True)
class IntelligenceDataset:
    """Canonical multi-repository assessment dataset for commercial reporting."""

    dataset_id: DatasetId
    name: str
    selection_method: str
    repository_count: int
    repository_assessments: tuple[RepositoryAssessmentReference, ...]
    included_repository_ids: tuple[str, ...]
    excluded_repositories: tuple[ExcludedRepository, ...] = ()
    assessment_schema_versions: tuple[str, ...] = ()
    assessment_time_range: AssessmentTimeRange = field(default_factory=AssessmentTimeRange)
    source_type_distribution: Mapping[str, int] = field(default_factory=dict)
    dataset_tags: tuple[str, ...] = ()
    limitations: tuple[DatasetLimitation, ...] = ()
    comparability_status: ComparabilityStatus = ComparabilityStatus.UNKNOWN
    selection_policy_version: str = DATASET_SELECTION_POLICY_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", bound_title(self.name))
        object.__setattr__(
            self,
            "selection_method",
            require_nonblank(self.selection_method, label="selection_method"),
        )
        object.__setattr__(
            self,
            "selection_policy_version",
            require_nonblank(self.selection_policy_version, label="selection_policy_version"),
        )
        assessments = tuple(
            sorted(
                self.repository_assessments,
                key=lambda item: (item.repository_id, item.assessment_id, item.assessment_run_id),
            )
        )
        object.__setattr__(self, "repository_assessments", assessments)
        repo_ids = [item.repository_id for item in assessments]
        if len(repo_ids) != len(set(repo_ids)):
            raise InvariantViolationError(
                "duplicate repository assessments are not allowed in one dataset",
                reason_code="duplicate_repository_assessment",
            )

        included = [
            item.repository_id
            for item in assessments
            if item.inclusion_status is InclusionStatus.INCLUDED
        ]
        expected_included = unique_sorted_ids(included, label="included_repository_id")
        provided = unique_sorted_ids(
            self.included_repository_ids, label="included_repository_id"
        )
        if provided != expected_included:
            raise InvariantViolationError(
                "included_repository_ids must reconcile with included assessments",
                reason_code="included_repository_mismatch",
            )
        if self.repository_count != len(expected_included):
            raise InvariantViolationError(
                "repository_count must equal included repository count",
                reason_code="repository_count_mismatch",
            )
        versions = optional_sorted_ids(
            self.assessment_schema_versions
            or tuple(item.assessment_schema_version for item in assessments),
            label="assessment_schema_version",
        )
        object.__setattr__(self, "assessment_schema_versions", versions)
        object.__setattr__(
            self, "dataset_tags", optional_sorted_ids(self.dataset_tags, label="dataset_tag")
        )
        object.__setattr__(
            self,
            "source_type_distribution",
            dict(sorted((str(k), int(v)) for k, v in self.source_type_distribution.items())),
        )
        expected_id = build_dataset_id(
            repository_assessment_refs=[item.identity_material() for item in assessments],
            selection_policy_version=self.selection_policy_version,
        )
        if self.dataset_id.value != expected_id.value:
            raise InvariantViolationError(
                "dataset_id does not match assessment references and selection policy",
                reason_code="unstable_dataset_id",
            )

    @classmethod
    def create(
        cls,
        *,
        name: str,
        selection_method: str,
        repository_assessments: Sequence[RepositoryAssessmentReference],
        excluded_repositories: Sequence[ExcludedRepository] = (),
        assessment_time_range: AssessmentTimeRange | None = None,
        source_type_distribution: Mapping[str, int] | None = None,
        dataset_tags: Sequence[str] = (),
        limitations: Sequence[DatasetLimitation] = (),
        comparability_status: ComparabilityStatus = ComparabilityStatus.UNKNOWN,
        selection_policy_version: str = DATASET_SELECTION_POLICY_VERSION,
    ) -> IntelligenceDataset:
        assessments = tuple(repository_assessments)
        included = tuple(
            sorted(
                {
                    item.repository_id
                    for item in assessments
                    if item.inclusion_status is InclusionStatus.INCLUDED
                }
            )
        )
        dist: dict[str, int] = {}
        if source_type_distribution is None:
            for item in assessments:
                if item.inclusion_status is InclusionStatus.INCLUDED:
                    key = item.source_type.value
                    dist[key] = dist.get(key, 0) + 1
        else:
            dist = dict(source_type_distribution)
        dataset_id = build_dataset_id(
            repository_assessment_refs=[item.identity_material() for item in assessments],
            selection_policy_version=selection_policy_version,
        )
        return cls(
            dataset_id=dataset_id,
            name=name,
            selection_method=selection_method,
            repository_count=len(included),
            repository_assessments=assessments,
            included_repository_ids=included,
            excluded_repositories=tuple(excluded_repositories),
            assessment_schema_versions=tuple(
                sorted({item.assessment_schema_version for item in assessments})
            ),
            assessment_time_range=assessment_time_range or AssessmentTimeRange(),
            source_type_distribution=dist,
            dataset_tags=tuple(dataset_tags),
            limitations=tuple(limitations),
            comparability_status=comparability_status,
            selection_policy_version=selection_policy_version,
        )
