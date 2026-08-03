"""Internal modernization observation candidate model."""

from __future__ import annotations

from dataclasses import dataclass, field

from codestrata_platform.intelligence_reporting.application.modernization_observations.identities import (
    ModernizationActionIdentity,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ConfidenceLevel,
    ModernizationObservationCategory,
)


@dataclass(frozen=True, slots=True)
class SupportRef:
    repository_id: str
    assessment_id: str
    entity_type: str
    entity_id: str
    confidence: ConfidenceLevel = ConfidenceLevel.UNAVAILABLE
    legacy_limited: bool = False
    comparable: bool = True
    finding_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


@dataclass
class ModernizationObservationCandidate:
    action: ModernizationActionIdentity
    category: ModernizationObservationCategory
    recommendation_refs: list[SupportRef] = field(default_factory=list)
    priority_action_refs: list[SupportRef] = field(default_factory=list)
    roadmap_refs: list[SupportRef] = field(default_factory=list)
    recurring_pattern_ids: list[str] = field(default_factory=list)
    supporting_finding_ids: set[str] = field(default_factory=set)
    supporting_evidence_ids: set[str] = field(default_factory=set)
    rejection_reason: str | None = None
    limitations: set[str] = field(default_factory=set)

    @property
    def candidate_id(self) -> str:
        return self.action.action_identity

    @property
    def repository_ids(self) -> tuple[str, ...]:
        repos = {item.repository_id for item in self.recommendation_refs}
        repos.update(item.repository_id for item in self.priority_action_refs)
        return tuple(sorted(repos))

    @property
    def repository_count(self) -> int:
        return len(self.repository_ids)

    @property
    def assessment_head_ids(self) -> tuple[str, ...]:
        return (self.action.assessment_head_id,)
