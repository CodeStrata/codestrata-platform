"""EngineeringIntelligenceReport root aggregate."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from codestrata_platform.domain.errors import InvariantViolationError, InvalidValueError
from codestrata_platform.intelligence_reporting.domain._safety import (
    bound_title,
    optional_sorted_ids,
)
from codestrata_platform.intelligence_reporting.domain.capability import (
    AssessmentHeadDistribution,
    CapabilityComparison,
)
from codestrata_platform.intelligence_reporting.domain.confidence import (
    IntelligenceReportConfidence,
)
from codestrata_platform.intelligence_reporting.domain.dataset import IntelligenceDataset
from codestrata_platform.intelligence_reporting.domain.drilldown import (
    RepositoryIntelligenceDrilldown,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ConfidenceLevel,
    DataVisibility,
    DerivationStatus,
    InclusionStatus,
    ReportScope,
)
from codestrata_platform.intelligence_reporting.domain.identifiers import (
    EngineeringIntelligenceReportId,
    build_report_id,
)
from codestrata_platform.intelligence_reporting.domain.limitations import DatasetLimitation
from codestrata_platform.intelligence_reporting.domain.modernization import (
    ModernizationObservation,
)
from codestrata_platform.intelligence_reporting.domain.patterns import (
    RecurringIntelligencePattern,
)
from codestrata_platform.intelligence_reporting.domain.repository_snapshot import (
    RepositoryPopulation,
)
from codestrata_platform.intelligence_reporting.domain.technology import TechnologyDistribution
from codestrata_platform.intelligence_reporting.domain.visibility import (
    WebsiteExportPolicy,
    WebsiteSafeIntelligenceReport,
)

ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION = "1.0"
ENGINEERING_INTELLIGENCE_REPORT_POLICY_VERSION = "intelligence-report-policy-v1"


@dataclass(frozen=True, slots=True)
class ReportExecutiveSummary:
    """Structured executive summary — no auto-generated narrative prose."""

    highlights: tuple[str, ...] = ()
    repository_count: int = 0
    pattern_count: int = 0
    modernization_observation_count: int = 0
    confidence_level: ConfidenceLevel = ConfidenceLevel.UNAVAILABLE
    limitation_count: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "highlights", optional_sorted_ids(self.highlights, label="highlight")
        )
        for name in (
            "repository_count",
            "pattern_count",
            "modernization_observation_count",
            "limitation_count",
        ):
            if getattr(self, name) < 0:
                raise InvalidValueError(
                    f"{name} must be non-negative",
                    reason_code=f"negative_{name}",
                )


@dataclass(frozen=True, slots=True)
class MethodologyNotes:
    notes: tuple[str, ...] = ()
    engine_assessment_schema_version: str = "1.2"
    report_schema_version: str = ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION
    methodology_id: str = "intelligence-report-methodology"
    methodology_version: str = "v1"
    interpretation_policy_bundle_id: str = ""
    aggregation_policy_id: str = ""
    oss_disclaimer: str = (
        "The public OSS dataset is used to validate the commercial "
        "intelligence-reporting model. It is not representative of all software "
        "repositories and must not be presented as a product-wide industry benchmark."
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "notes", optional_sorted_ids(self.notes, label="methodology_note"))
        object.__setattr__(
            self,
            "interpretation_policy_bundle_id",
            (self.interpretation_policy_bundle_id or "").strip(),
        )
        object.__setattr__(
            self, "aggregation_policy_id", (self.aggregation_policy_id or "").strip()
        )


@dataclass(frozen=True, slots=True)
class GeneratedArtifactMetadata:
    """Non-identity metadata about generated artifacts (paths forbidden)."""

    artifact_kinds: tuple[str, ...] = ()
    content_hashes: tuple[str, ...] = ()
    generator_version: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "artifact_kinds", optional_sorted_ids(self.artifact_kinds, label="artifact_kind")
        )
        object.__setattr__(
            self,
            "content_hashes",
            optional_sorted_ids(self.content_hashes, label="content_hash"),
        )


@dataclass(frozen=True, slots=True)
class EngineeringIntelligenceReport:
    """Canonical commercial multi-repository Engineering Intelligence Report."""

    report_id: EngineeringIntelligenceReportId
    schema_version: str
    title: str
    report_scope: ReportScope
    dataset: IntelligenceDataset
    executive_summary: ReportExecutiveSummary = field(default_factory=ReportExecutiveSummary)
    repository_population: RepositoryPopulation = field(default_factory=RepositoryPopulation)
    technology_distribution: TechnologyDistribution = field(
        default_factory=TechnologyDistribution
    )
    capability_comparisons: tuple[CapabilityComparison, ...] = ()
    recurring_patterns: tuple[RecurringIntelligencePattern, ...] = ()
    assessment_head_distributions: tuple[AssessmentHeadDistribution, ...] = ()
    modernization_observations: tuple[ModernizationObservation, ...] = ()
    repository_drilldowns: tuple[RepositoryIntelligenceDrilldown, ...] = ()
    confidence: IntelligenceReportConfidence = field(
        default_factory=lambda: IntelligenceReportConfidence(
            level=ConfidenceLevel.UNAVAILABLE,
            basis=(),
            derivation_status=DerivationStatus.DEFERRED,
            limitations=(
                "Report confidence derivation deferred until report-quality evaluation.",
            ),
        )
    )
    limitations: tuple[DatasetLimitation, ...] = ()
    methodology: MethodologyNotes = field(default_factory=MethodologyNotes)
    generated_artifact_metadata: GeneratedArtifactMetadata = field(
        default_factory=GeneratedArtifactMetadata
    )
    report_policy_version: str = ENGINEERING_INTELLIGENCE_REPORT_POLICY_VERSION
    interpretation_policy_bundle_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", bound_title(self.title))
        if self.schema_version != ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION:
            raise InvalidValueError(
                f"unsupported commercial report schema version: {self.schema_version}",
                reason_code="unsupported_eir_schema_version",
            )
        included = set(self.dataset.included_repository_ids)
        for pattern in self.recurring_patterns:
            missing = set(pattern.repository_ids) - included
            if missing:
                raise InvariantViolationError(
                    f"pattern references repositories outside dataset: {sorted(missing)}",
                    reason_code="pattern_repo_not_in_dataset",
                )
        for observation in self.modernization_observations:
            missing = set(observation.repository_ids) - included
            if missing:
                raise InvariantViolationError(
                    f"observation references repositories outside dataset: {sorted(missing)}",
                    reason_code="observation_repo_not_in_dataset",
                )
        drilldowns = tuple(
            sorted(
                self.repository_drilldowns,
                key=lambda item: (item.repository_id, item.assessment_id),
            )
        )
        object.__setattr__(self, "repository_drilldowns", drilldowns)
        seen_drill: set[str] = set()
        for item in drilldowns:
            if item.repository_id not in included:
                raise InvariantViolationError(
                    "drilldown repository is not included in dataset",
                    reason_code="drilldown_repo_not_in_dataset",
                )
            if item.repository_id in seen_drill:
                raise InvariantViolationError(
                    "duplicate drilldown for repository",
                    reason_code="duplicate_drilldown",
                )
            seen_drill.add(item.repository_id)
        for limitation in self.limitations:
            missing = set(limitation.affected_repository_ids) - included
            if missing:
                raise InvariantViolationError(
                    f"limitation references unknown repositories: {sorted(missing)}",
                    reason_code="limitation_repo_not_in_dataset",
                )
        runs = tuple(
            sorted(
                {
                    f"{item.repository_id}:{item.assessment_run_id}"
                    for item in self.dataset.repository_assessments
                    if item.repository_id in included
                }
            )
        )
        expected = build_report_id(
            dataset_id=self.dataset.dataset_id.value,
            schema_version=self.schema_version,
            report_scope=self.report_scope.value,
            assessment_run_identities=runs,
            report_policy_version=self.report_policy_version,
            interpretation_policy_bundle_id=self.interpretation_policy_bundle_id,
        )
        if self.report_id.value != expected.value:
            raise InvariantViolationError(
                "report_id does not match dataset/scope/policy/assessment runs/bundle",
                reason_code="unstable_report_id",
            )
        object.__setattr__(
            self,
            "interpretation_policy_bundle_id",
            (self.interpretation_policy_bundle_id or "").strip(),
        )
        object.__setattr__(
            self,
            "capability_comparisons",
            tuple(sorted(self.capability_comparisons, key=lambda item: item.assessment_head_id)),
        )
        object.__setattr__(
            self,
            "recurring_patterns",
            tuple(sorted(self.recurring_patterns, key=lambda item: item.pattern_id.value)),
        )
        object.__setattr__(
            self,
            "assessment_head_distributions",
            tuple(
                sorted(
                    self.assessment_head_distributions,
                    key=lambda item: item.assessment_head_id,
                )
            ),
        )
        object.__setattr__(
            self,
            "modernization_observations",
            tuple(
                sorted(
                    self.modernization_observations,
                    key=lambda item: item.observation_id.value,
                )
            ),
        )

    @classmethod
    def create(
        cls,
        *,
        title: str,
        report_scope: ReportScope,
        dataset: IntelligenceDataset,
        executive_summary: ReportExecutiveSummary | None = None,
        repository_population: RepositoryPopulation | None = None,
        technology_distribution: TechnologyDistribution | None = None,
        capability_comparisons: Sequence[CapabilityComparison] = (),
        recurring_patterns: Sequence[RecurringIntelligencePattern] = (),
        assessment_head_distributions: Sequence[AssessmentHeadDistribution] = (),
        modernization_observations: Sequence[ModernizationObservation] = (),
        repository_drilldowns: Sequence[RepositoryIntelligenceDrilldown] = (),
        confidence: IntelligenceReportConfidence | None = None,
        limitations: Sequence[DatasetLimitation] = (),
        methodology: MethodologyNotes | None = None,
        generated_artifact_metadata: GeneratedArtifactMetadata | None = None,
        report_policy_version: str = ENGINEERING_INTELLIGENCE_REPORT_POLICY_VERSION,
        schema_version: str = ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION,
        interpretation_policy_bundle_id: str = "",
    ) -> EngineeringIntelligenceReport:
        included = set(dataset.included_repository_ids)
        runs = tuple(
            sorted(
                {
                    f"{item.repository_id}:{item.assessment_run_id}"
                    for item in dataset.repository_assessments
                    if item.repository_id in included
                }
            )
        )
        bundle_id = (interpretation_policy_bundle_id or "").strip()
        report_id = build_report_id(
            dataset_id=dataset.dataset_id.value,
            schema_version=schema_version,
            report_scope=report_scope.value,
            assessment_run_identities=runs,
            report_policy_version=report_policy_version,
            interpretation_policy_bundle_id=bundle_id,
        )
        return cls(
            report_id=report_id,
            schema_version=schema_version,
            title=title,
            report_scope=report_scope,
            dataset=dataset,
            executive_summary=executive_summary
            or ReportExecutiveSummary(repository_count=dataset.repository_count),
            repository_population=repository_population
            or RepositoryPopulation(
                repository_count=dataset.repository_count,
                included_repository_ids=dataset.included_repository_ids,
            ),
            technology_distribution=technology_distribution or TechnologyDistribution(),
            capability_comparisons=tuple(capability_comparisons),
            recurring_patterns=tuple(recurring_patterns),
            assessment_head_distributions=tuple(assessment_head_distributions),
            modernization_observations=tuple(modernization_observations),
            repository_drilldowns=tuple(repository_drilldowns),
            confidence=confidence
            or IntelligenceReportConfidence(
                level=ConfidenceLevel.UNAVAILABLE,
                basis=(),
                repository_sample_count=dataset.repository_count,
                derivation_status=DerivationStatus.DEFERRED,
                limitations=(
                    "Report confidence derivation deferred until report-quality evaluation.",
                ),
            ),
            limitations=tuple(limitations),
            methodology=methodology or MethodologyNotes(),
            generated_artifact_metadata=generated_artifact_metadata
            or GeneratedArtifactMetadata(),
            report_policy_version=report_policy_version,
            interpretation_policy_bundle_id=bundle_id,
        )

    def to_website_safe(
        self,
        policy: WebsiteExportPolicy | None = None,
    ) -> WebsiteSafeIntelligenceReport:
        """Project into a website-safe export DTO (no HTML renderer)."""

        active_policy = policy or WebsiteExportPolicy()
        public_ids: list[str] = []
        anonymized_ids: list[str] = []
        display_names: list[str] = []
        for index, item in enumerate(self.dataset.repository_assessments, start=1):
            if item.inclusion_status is not InclusionStatus.INCLUDED:
                continue
            if item.visibility is DataVisibility.PUBLIC:
                if item.source_reference and not item.source_reference_publication_permitted:
                    raise InvariantViolationError(
                        "public repository lacks publication permission for website export",
                        reason_code="public_repo_publication_denied",
                    )
                if (
                    active_policy.preferred_visibility_mode is DataVisibility.ANONYMIZED
                    or not active_policy.allow_public_repository_names
                ):
                    anonymized_ids.append(item.repository_id)
                    display_names.append(f"repository-{index:02d}")
                else:
                    public_ids.append(item.repository_id)
                    if item.display_name:
                        display_names.append(item.display_name)
                    else:
                        display_names.append(item.repository_id)
            elif item.visibility is DataVisibility.ANONYMIZED:
                anonymized_ids.append(item.repository_id)
                display_names.append(f"repository-{index:02d}")
            elif item.visibility in {
                DataVisibility.CUSTOMER_PRIVATE,
                DataVisibility.INTERNAL,
            }:
                if active_policy.forbid_private_repository_names and (
                    item.display_name or active_policy.preferred_visibility_mode is DataVisibility.PUBLIC
                ):
                    raise InvariantViolationError(
                        "private repository display names cannot enter website-safe export",
                        reason_code="private_repository_name_rejected",
                    )
                if active_policy.allow_anonymized_repository_identifiers:
                    anonymized_ids.append(item.repository_id)
                    display_names.append(f"repository-{index:02d}")
                else:
                    raise InvariantViolationError(
                        "private repository cannot enter website-safe export",
                        reason_code="private_repository_rejected",
                    )
        visibility_mode = active_policy.preferred_visibility_mode.value
        if anonymized_ids and not public_ids:
            visibility_mode = DataVisibility.ANONYMIZED.value
        elif public_ids and not anonymized_ids:
            visibility_mode = DataVisibility.PUBLIC.value
        safe = WebsiteSafeIntelligenceReport(
            report_id=self.report_id.value,
            schema_version=self.schema_version,
            report_scope=self.report_scope.value,
            dataset_id=self.dataset.dataset_id.value,
            visibility_mode=visibility_mode,
            included_repository_ids=self.dataset.included_repository_ids,
            public_repository_ids=tuple(public_ids),
            anonymized_repository_ids=tuple(anonymized_ids),
            public_repository_display_names=tuple(display_names),
            aggregated_counts={
                "repository_count": self.dataset.repository_count,
                "pattern_count": len(self.recurring_patterns),
                "modernization_observation_count": len(self.modernization_observations),
            },
            safe_technology_names=tuple(
                item.normalized_name for item in self.technology_distribution.observations
            ),
            safe_observation_titles=tuple(item.title for item in self.modernization_observations),
            methodology_notes=self.methodology.notes,
            confidence_level=self.confidence.level.value,
            customer_visible_limitations=tuple(
                item.statement for item in self.limitations if item.customer_visible
            ),
            policy=active_policy,
        )
        active_policy.assert_payload_safe(
            {
                "report_id": safe.report_id,
                "dataset_id": safe.dataset_id,
                "aggregated_counts": dict(safe.aggregated_counts),
            }
        )
        return safe
