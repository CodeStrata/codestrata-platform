"""Executive metric, finding, recommendation, and observation value objects."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.executive_intelligence.identifiers import (
    ExecutiveFindingId,
    ExecutiveMetricId,
    ExecutiveRecommendationId,
)
from codestrata_platform.domain.executive_intelligence.lifecycle import (
    ExecutiveConfidenceBand,
    ExecutiveFindingCategory,
    ExecutiveImpactBand,
    ExecutiveMetricKey,
    ExecutiveRecommendationTheme,
)


def _clamp_score(value: int) -> int:
    return max(0, min(100, int(value)))


def _clamp_ratio(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True, slots=True)
class ExecutiveMetric:
    """Deterministic portfolio-level executive metric."""

    metric_id: ExecutiveMetricId
    key: ExecutiveMetricKey
    score: int
    confidence: float
    confidence_band: ExecutiveConfidenceBand
    coverage: float
    inputs: tuple[str, ...]
    calculation_rule: str
    limitations: tuple[str, ...]
    policy_version: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "score", _clamp_score(self.score))
        object.__setattr__(self, "confidence", _clamp_ratio(self.confidence))
        object.__setattr__(self, "coverage", _clamp_ratio(self.coverage))
        if not self.calculation_rule.strip():
            raise InvalidValueError(
                "calculation_rule must be non-blank",
                reason_code="empty_executive_metric_rule",
            )


@dataclass(frozen=True, slots=True)
class ExecutiveFinding:
    """Deterministic executive finding grounded in Portfolio Intelligence."""

    finding_id: ExecutiveFindingId
    category: ExecutiveFindingCategory
    title: str
    summary: str
    severity_band: ExecutiveImpactBand
    confidence: float
    confidence_band: ExecutiveConfidenceBand
    affected_repository_ids: tuple[str, ...]
    source_references: tuple[str, ...]
    evidence: tuple[str, ...]
    policy_version: str

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise InvalidValueError(
                "finding title must be non-blank",
                reason_code="empty_executive_finding_title",
            )
        object.__setattr__(self, "confidence", _clamp_ratio(self.confidence))
        object.__setattr__(self, "title", self.title.strip()[:240])
        object.__setattr__(self, "summary", self.summary.strip()[:2000])


@dataclass(frozen=True, slots=True)
class ExecutiveRecommendation:
    """Deterministic executive recommendation grounded in Portfolio Intelligence."""

    recommendation_id: ExecutiveRecommendationId
    theme: ExecutiveRecommendationTheme
    title: str
    rationale: str
    affected_repository_ids: tuple[str, ...]
    confidence: float
    confidence_band: ExecutiveConfidenceBand
    expected_impact: ExecutiveImpactBand
    source_references: tuple[str, ...]
    priority_score: int
    policy_version: str

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise InvalidValueError(
                "recommendation title must be non-blank",
                reason_code="empty_executive_recommendation_title",
            )
        if not self.rationale.strip():
            raise InvalidValueError(
                "recommendation rationale must be non-blank",
                reason_code="empty_executive_recommendation_rationale",
            )
        object.__setattr__(self, "confidence", _clamp_ratio(self.confidence))
        object.__setattr__(self, "priority_score", _clamp_score(self.priority_score))
        object.__setattr__(self, "title", self.title.strip()[:240])
        object.__setattr__(self, "rationale", self.rationale.strip()[:4000])


@dataclass(frozen=True, slots=True)
class StrategicObservation:
    """Bounded strategic observation derived from metrics and findings."""

    observation_key: str
    title: str
    summary: str
    related_metric_keys: tuple[str, ...]
    related_finding_ids: tuple[str, ...]
    confidence: float
    confidence_band: ExecutiveConfidenceBand

    def __post_init__(self) -> None:
        if not self.observation_key.strip():
            raise InvalidValueError(
                "observation_key must be non-blank",
                reason_code="empty_strategic_observation_key",
            )
        object.__setattr__(self, "confidence", _clamp_ratio(self.confidence))
        object.__setattr__(self, "observation_key", self.observation_key.strip()[:128])
        object.__setattr__(self, "title", self.title.strip()[:240])
        object.__setattr__(self, "summary", self.summary.strip()[:2000])
