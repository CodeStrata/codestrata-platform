"""Modernization observations (not portfolio Recommendations)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.domain._safety import (
    bound_statement,
    bound_title,
    optional_sorted_ids,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ConfidenceLevel,
    ModernizationObservationCategory,
)
from codestrata_platform.intelligence_reporting.domain.identifiers import (
    ObservationId,
    build_observation_id,
)

MODERNIZATION_OBSERVATION_POLICY_VERSION = "intelligence-modernization-observation-v1"

_FORBIDDEN_FIELD_MARKERS = (
    "roi",
    "cost_usd",
    "staffing",
    "migration_duration",
    "delivery_commitment",
)


@dataclass(frozen=True, slots=True)
class ModernizationObservation:
    """Cross-repository modernization synthesis backed by deterministic actions."""

    observation_id: ObservationId
    title: str
    statement: str
    category: ModernizationObservationCategory
    assessment_head_ids: tuple[str, ...] = ()
    repository_ids: tuple[str, ...] = ()
    recommendation_ids: tuple[str, ...] = ()
    priority_action_ids: tuple[str, ...] = ()
    roadmap_initiative_ids: tuple[str, ...] = ()
    supporting_finding_ids: tuple[str, ...] = ()
    supporting_evidence_ids: tuple[str, ...] = ()
    repository_count: int = 0
    confidence: ConfidenceLevel = ConfidenceLevel.UNAVAILABLE
    limitations: tuple[str, ...] = ()
    drilldown_refs: tuple[str, ...] = ()
    normalized_subject: str = ""
    policy_version: str = MODERNIZATION_OBSERVATION_POLICY_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", bound_title(self.title))
        object.__setattr__(self, "statement", bound_statement(self.statement))
        subject = (self.normalized_subject or self.title).strip()
        object.__setattr__(self, "normalized_subject", subject)
        object.__setattr__(
            self,
            "assessment_head_ids",
            optional_sorted_ids(self.assessment_head_ids, label="assessment_head_id"),
        )
        repos = optional_sorted_ids(self.repository_ids, label="repository_id")
        object.__setattr__(self, "repository_ids", repos)
        recs = optional_sorted_ids(self.recommendation_ids, label="recommendation_id")
        object.__setattr__(self, "recommendation_ids", recs)
        actions = optional_sorted_ids(self.priority_action_ids, label="priority_action_id")
        object.__setattr__(self, "priority_action_ids", actions)
        object.__setattr__(
            self,
            "roadmap_initiative_ids",
            optional_sorted_ids(self.roadmap_initiative_ids, label="roadmap_initiative_id"),
        )
        object.__setattr__(
            self,
            "supporting_finding_ids",
            optional_sorted_ids(self.supporting_finding_ids, label="supporting_finding_id"),
        )
        object.__setattr__(
            self,
            "supporting_evidence_ids",
            optional_sorted_ids(self.supporting_evidence_ids, label="supporting_evidence_id"),
        )
        object.__setattr__(
            self, "limitations", optional_sorted_ids(self.limitations, label="limitation")
        )
        object.__setattr__(
            self,
            "drilldown_refs",
            optional_sorted_ids(self.drilldown_refs, label="drilldown_ref"),
        )
        if self.repository_count != len(repos):
            raise InvalidValueError(
                "repository_count must equal repository_ids length",
                reason_code="observation_repository_count_mismatch",
            )
        if not recs and not actions:
            raise InvalidValueError(
                "modernization observation requires recommendation or priority-action support",
                reason_code="observation_missing_deterministic_support",
            )
        lowered = f"{self.title} {self.statement}".lower()
        for marker in _FORBIDDEN_FIELD_MARKERS:
            if marker in lowered:
                raise InvalidValueError(
                    "modernization observations must not assert ROI/cost/staffing/duration",
                    reason_code="forbidden_business_claim",
                )
        expected = build_observation_id(
            category=self.category.value,
            normalized_subject=subject,
            repository_ids=repos,
            recommendation_ids=recs,
            priority_action_ids=actions,
            policy_version=self.policy_version,
        )
        if self.observation_id.value != expected.value:
            raise InvalidValueError(
                "observation_id does not match deterministic identity inputs",
                reason_code="unstable_observation_id",
            )

    @classmethod
    def create(
        cls,
        *,
        title: str,
        statement: str,
        category: ModernizationObservationCategory,
        repository_ids: Sequence[str],
        recommendation_ids: Sequence[str] = (),
        priority_action_ids: Sequence[str] = (),
        assessment_head_ids: Sequence[str] = (),
        roadmap_initiative_ids: Sequence[str] = (),
        supporting_finding_ids: Sequence[str] = (),
        supporting_evidence_ids: Sequence[str] = (),
        confidence: ConfidenceLevel = ConfidenceLevel.UNAVAILABLE,
        limitations: Sequence[str] = (),
        drilldown_refs: Sequence[str] = (),
        normalized_subject: str = "",
        policy_version: str = MODERNIZATION_OBSERVATION_POLICY_VERSION,
    ) -> ModernizationObservation:
        repos = optional_sorted_ids(repository_ids, label="repository_id")
        recs = optional_sorted_ids(recommendation_ids, label="recommendation_id")
        actions = optional_sorted_ids(priority_action_ids, label="priority_action_id")
        subject = (normalized_subject or title).strip()
        observation_id = build_observation_id(
            category=category.value,
            normalized_subject=subject,
            repository_ids=repos,
            recommendation_ids=recs,
            priority_action_ids=actions,
            policy_version=policy_version,
        )
        return cls(
            observation_id=observation_id,
            title=title,
            statement=statement,
            category=category,
            assessment_head_ids=tuple(assessment_head_ids),
            repository_ids=repos,
            recommendation_ids=recs,
            priority_action_ids=actions,
            roadmap_initiative_ids=tuple(roadmap_initiative_ids),
            supporting_finding_ids=tuple(supporting_finding_ids),
            supporting_evidence_ids=tuple(supporting_evidence_ids),
            repository_count=len(repos),
            confidence=confidence,
            limitations=tuple(limitations),
            drilldown_refs=tuple(drilldown_refs),
            normalized_subject=subject,
            policy_version=policy_version,
        )
