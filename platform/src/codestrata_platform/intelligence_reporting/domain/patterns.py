"""Recurring intelligence pattern model."""

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
    PatternType,
)
from codestrata_platform.intelligence_reporting.domain.identifiers import (
    PatternId,
    build_pattern_id,
)
from codestrata_platform.intelligence_reporting.domain.technology import Ratio

PATTERN_POLICY_VERSION = "intelligence-pattern-policy-v1"


@dataclass(frozen=True, slots=True)
class RecurringIntelligencePattern:
    pattern_id: PatternId
    pattern_type: PatternType
    title: str
    statement: str
    assessment_head_ids: tuple[str, ...] = ()
    rule_ids: tuple[str, ...] = ()
    repository_ids: tuple[str, ...] = ()
    assessment_ids: tuple[str, ...] = ()
    finding_ids: tuple[str, ...] = ()
    recommendation_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    repository_count: int = 0
    repository_ratio: Ratio | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.UNAVAILABLE
    limitations: tuple[str, ...] = ()
    drilldown_refs: tuple[str, ...] = ()
    normalized_subject: str = ""
    policy_version: str = PATTERN_POLICY_VERSION
    allow_single_repository: bool = False

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
        object.__setattr__(
            self, "rule_ids", optional_sorted_ids(self.rule_ids, label="rule_id")
        )
        repos = optional_sorted_ids(self.repository_ids, label="repository_id")
        object.__setattr__(self, "repository_ids", repos)
        object.__setattr__(
            self,
            "assessment_ids",
            optional_sorted_ids(self.assessment_ids, label="assessment_id"),
        )
        object.__setattr__(
            self, "finding_ids", optional_sorted_ids(self.finding_ids, label="finding_id")
        )
        object.__setattr__(
            self,
            "recommendation_ids",
            optional_sorted_ids(self.recommendation_ids, label="recommendation_id"),
        )
        object.__setattr__(
            self, "evidence_ids", optional_sorted_ids(self.evidence_ids, label="evidence_id")
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
                reason_code="pattern_repository_count_mismatch",
            )
        if self.repository_count < 2 and not self.allow_single_repository:
            raise InvalidValueError(
                "recurring patterns require at least two repositories unless explicitly allowed",
                reason_code="pattern_requires_multiple_repositories",
            )
        expected = build_pattern_id(
            pattern_type=self.pattern_type.value,
            normalized_subject=subject,
            rule_ids=self.rule_ids,
            assessment_head_ids=self.assessment_head_ids,
            repository_ids=repos,
            policy_version=self.policy_version,
        )
        if self.pattern_id.value != expected.value:
            raise InvalidValueError(
                "pattern_id does not match deterministic identity inputs",
                reason_code="unstable_pattern_id",
            )

    @classmethod
    def create(
        cls,
        *,
        pattern_type: PatternType,
        title: str,
        statement: str,
        repository_ids: Sequence[str],
        normalized_subject: str = "",
        assessment_head_ids: Sequence[str] = (),
        rule_ids: Sequence[str] = (),
        assessment_ids: Sequence[str] = (),
        finding_ids: Sequence[str] = (),
        recommendation_ids: Sequence[str] = (),
        evidence_ids: Sequence[str] = (),
        repository_ratio: Ratio | None = None,
        confidence: ConfidenceLevel = ConfidenceLevel.UNAVAILABLE,
        limitations: Sequence[str] = (),
        drilldown_refs: Sequence[str] = (),
        policy_version: str = PATTERN_POLICY_VERSION,
        allow_single_repository: bool = False,
    ) -> RecurringIntelligencePattern:
        repos = optional_sorted_ids(repository_ids, label="repository_id")
        subject = (normalized_subject or title).strip()
        pattern_id = build_pattern_id(
            pattern_type=pattern_type.value,
            normalized_subject=subject,
            rule_ids=rule_ids,
            assessment_head_ids=assessment_head_ids,
            repository_ids=repos,
            policy_version=policy_version,
        )
        return cls(
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            title=title,
            statement=statement,
            assessment_head_ids=tuple(assessment_head_ids),
            rule_ids=tuple(rule_ids),
            repository_ids=repos,
            assessment_ids=tuple(assessment_ids),
            finding_ids=tuple(finding_ids),
            recommendation_ids=tuple(recommendation_ids),
            evidence_ids=tuple(evidence_ids),
            repository_count=len(repos),
            repository_ratio=repository_ratio,
            confidence=confidence,
            limitations=tuple(limitations),
            drilldown_refs=tuple(drilldown_refs),
            normalized_subject=subject,
            policy_version=policy_version,
            allow_single_repository=allow_single_repository,
        )
