"""Bounded repository drill-down references (no source bodies / snippets)."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.domain._safety import (
    bound_title,
    optional_sorted_ids,
    reject_unsafe_text,
    require_nonblank,
)
from codestrata_platform.intelligence_reporting.domain.capability import (
    RepositoryCapabilitySnapshot,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ConfidenceLevel,
    DataVisibility,
    SourceType,
)
from codestrata_platform.intelligence_reporting.domain.identifiers import (
    DrilldownId,
    build_drilldown_id,
)


@dataclass(frozen=True, slots=True)
class SafeEntityRef:
    """Bounded reference to a finding/recommendation/action in a source assessment."""

    entity_id: str
    assessment_id: str
    entity_kind: str
    label: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "entity_id", require_nonblank(self.entity_id, label="entity_id"))
        object.__setattr__(
            self, "assessment_id", require_nonblank(self.assessment_id, label="assessment_id")
        )
        object.__setattr__(
            self, "entity_kind", require_nonblank(self.entity_kind, label="entity_kind").lower()
        )
        if self.label is not None:
            object.__setattr__(self, "label", bound_title(self.label))


@dataclass(frozen=True, slots=True)
class RepositoryIntelligenceDrilldown:
    drilldown_id: DrilldownId
    repository_id: str
    assessment_id: str
    display_name: str
    source_type: SourceType
    visibility: DataVisibility
    technology_summary: tuple[str, ...] = ()
    assessment_head_snapshots: tuple[RepositoryCapabilitySnapshot, ...] = ()
    recurring_pattern_ids: tuple[str, ...] = ()
    modernization_observation_ids: tuple[str, ...] = ()
    highest_priority_action_ids: tuple[str, ...] = ()
    finding_refs: tuple[SafeEntityRef, ...] = ()
    recommendation_refs: tuple[SafeEntityRef, ...] = ()
    confidence: ConfidenceLevel = ConfidenceLevel.UNAVAILABLE
    limitations: tuple[str, ...] = ()
    canonical_assessment_report_ref: str | None = None
    # Additive Slice 6.9 identity / navigation fields (EIR 1.0 compatible).
    assessment_run_id: str = ""
    dataset_id: str = ""
    canonical_report_digest: str = ""
    policy_id: str = ""
    priority_action_refs: tuple[SafeEntityRef, ...] = ()
    roadmap_refs: tuple[SafeEntityRef, ...] = ()
    correlation_refs: tuple[SafeEntityRef, ...] = ()
    public_export_eligible: bool = False
    requires_anonymization: bool = False
    website_export_blocking_reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "repository_id", require_nonblank(self.repository_id, label="repository_id")
        )
        object.__setattr__(
            self, "assessment_id", require_nonblank(self.assessment_id, label="assessment_id")
        )
        object.__setattr__(self, "display_name", bound_title(self.display_name))
        object.__setattr__(self, "assessment_run_id", (self.assessment_run_id or "").strip())
        object.__setattr__(self, "dataset_id", (self.dataset_id or "").strip())
        object.__setattr__(
            self, "canonical_report_digest", (self.canonical_report_digest or "").strip()
        )
        object.__setattr__(self, "policy_id", (self.policy_id or "").strip())
        expected = build_drilldown_id(
            repository_id=self.repository_id,
            assessment_id=self.assessment_id,
            assessment_run_id=self.assessment_run_id,
            dataset_id=self.dataset_id,
            canonical_report_digest=self.canonical_report_digest,
            policy_token=self.policy_id,
        )
        if self.drilldown_id.value != expected.value:
            raise InvalidValueError(
                "drilldown_id does not match repository/assessment identity",
                reason_code="unstable_drilldown_id",
            )
        object.__setattr__(
            self,
            "technology_summary",
            optional_sorted_ids(self.technology_summary, label="technology_summary"),
        )
        object.__setattr__(
            self,
            "recurring_pattern_ids",
            optional_sorted_ids(self.recurring_pattern_ids, label="recurring_pattern_id"),
        )
        object.__setattr__(
            self,
            "modernization_observation_ids",
            optional_sorted_ids(
                self.modernization_observation_ids, label="modernization_observation_id"
            ),
        )
        object.__setattr__(
            self,
            "highest_priority_action_ids",
            optional_sorted_ids(
                self.highest_priority_action_ids, label="highest_priority_action_id"
            ),
        )
        object.__setattr__(
            self, "limitations", optional_sorted_ids(self.limitations, label="limitation")
        )
        object.__setattr__(
            self,
            "website_export_blocking_reasons",
            optional_sorted_ids(
                self.website_export_blocking_reasons, label="website_export_blocking_reason"
            ),
        )
        snaps = tuple(
            sorted(
                self.assessment_head_snapshots,
                key=lambda item: item.assessment_head_id,
            )
        )
        for item in snaps:
            if item.repository_id != self.repository_id:
                raise InvalidValueError(
                    "drilldown capability snapshot repository_id mismatch",
                    reason_code="drilldown_snapshot_repo_mismatch",
                )
        object.__setattr__(self, "assessment_head_snapshots", snaps)
        for refs_attr in (
            "finding_refs",
            "recommendation_refs",
            "priority_action_refs",
            "roadmap_refs",
            "correlation_refs",
        ):
            refs = tuple(
                sorted(getattr(self, refs_attr), key=lambda item: (item.entity_kind, item.entity_id))
            )
            for item in refs:
                if item.assessment_id != self.assessment_id:
                    raise InvalidValueError(
                        "drilldown entity refs must identify the source assessment",
                        reason_code="drilldown_ref_assessment_mismatch",
                    )
            object.__setattr__(self, refs_attr, refs)
        if self.canonical_assessment_report_ref is not None:
            object.__setattr__(
                self,
                "canonical_assessment_report_ref",
                reject_unsafe_text(
                    self.canonical_assessment_report_ref,
                    label="canonical_assessment_report_ref",
                ),
            )
        if self.visibility is DataVisibility.PUBLIC and not self.display_name:
            raise InvalidValueError(
                "public drilldown requires display_name",
                reason_code="public_drilldown_missing_display_name",
            )

    @classmethod
    def create(
        cls,
        *,
        repository_id: str,
        assessment_id: str,
        display_name: str,
        source_type: SourceType,
        visibility: DataVisibility,
        technology_summary: tuple[str, ...] = (),
        assessment_head_snapshots: tuple[RepositoryCapabilitySnapshot, ...] = (),
        recurring_pattern_ids: tuple[str, ...] = (),
        modernization_observation_ids: tuple[str, ...] = (),
        highest_priority_action_ids: tuple[str, ...] = (),
        finding_refs: tuple[SafeEntityRef, ...] = (),
        recommendation_refs: tuple[SafeEntityRef, ...] = (),
        confidence: ConfidenceLevel = ConfidenceLevel.UNAVAILABLE,
        limitations: tuple[str, ...] = (),
        canonical_assessment_report_ref: str | None = None,
        assessment_run_id: str = "",
        dataset_id: str = "",
        canonical_report_digest: str = "",
        policy_id: str = "",
        priority_action_refs: tuple[SafeEntityRef, ...] = (),
        roadmap_refs: tuple[SafeEntityRef, ...] = (),
        correlation_refs: tuple[SafeEntityRef, ...] = (),
        public_export_eligible: bool = False,
        requires_anonymization: bool = False,
        website_export_blocking_reasons: tuple[str, ...] = (),
    ) -> RepositoryIntelligenceDrilldown:
        return cls(
            drilldown_id=build_drilldown_id(
                repository_id=repository_id,
                assessment_id=assessment_id,
                assessment_run_id=assessment_run_id,
                dataset_id=dataset_id,
                canonical_report_digest=canonical_report_digest,
                policy_token=policy_id,
            ),
            repository_id=repository_id,
            assessment_id=assessment_id,
            display_name=display_name,
            source_type=source_type,
            visibility=visibility,
            technology_summary=technology_summary,
            assessment_head_snapshots=assessment_head_snapshots,
            recurring_pattern_ids=recurring_pattern_ids,
            modernization_observation_ids=modernization_observation_ids,
            highest_priority_action_ids=highest_priority_action_ids,
            finding_refs=finding_refs,
            recommendation_refs=recommendation_refs,
            confidence=confidence,
            limitations=limitations,
            canonical_assessment_report_ref=canonical_assessment_report_ref,
            assessment_run_id=assessment_run_id,
            dataset_id=dataset_id,
            canonical_report_digest=canonical_report_digest,
            policy_id=policy_id,
            priority_action_refs=priority_action_refs,
            roadmap_refs=roadmap_refs,
            correlation_refs=correlation_refs,
            public_export_eligible=public_export_eligible,
            requires_anonymization=requires_anonymization,
            website_export_blocking_reasons=website_export_blocking_reasons,
        )
