"""Internal pattern occurrence and candidate models."""

from __future__ import annotations

from dataclasses import dataclass, field

from codestrata_platform.intelligence_reporting.application.recurring_patterns.identities import (
    RecurringPatternSubject,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ConfidenceLevel,
    PatternType,
)


@dataclass(frozen=True, slots=True)
class RecurringPatternOccurrence:
    repository_id: str
    assessment_id: str
    entity_type: str
    entity_id: str
    rule_id: str | None = None
    assessment_head_id: str | None = None
    normalized_subject: str = ""
    evidence_ids: tuple[str, ...] = ()
    finding_ids: tuple[str, ...] = ()
    recommendation_ids: tuple[str, ...] = ()
    priority_action_ids: tuple[str, ...] = ()
    source_fact_ref: str | None = None
    legacy_limited: bool = False
    comparable: bool = True
    confidence_support: ConfidenceLevel = ConfidenceLevel.UNAVAILABLE
    limitations: tuple[str, ...] = ()


@dataclass
class PatternCandidate:
    pattern_type: PatternType
    subject: RecurringPatternSubject
    occurrences: list[RecurringPatternOccurrence] = field(default_factory=list)
    rejection_reason: str | None = None

    @property
    def repository_ids(self) -> tuple[str, ...]:
        return tuple(sorted({item.repository_id for item in self.occurrences}))

    @property
    def repository_count(self) -> int:
        return len(self.repository_ids)

    @property
    def occurrence_count(self) -> int:
        return len(self.occurrences)
