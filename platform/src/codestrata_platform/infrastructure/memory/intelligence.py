"""In-memory assessment intelligence repositories."""

from __future__ import annotations

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.intelligence.aggregate import AssessmentIntelligence
from codestrata_platform.domain.intelligence.ids import (
    AssessmentIntelligenceId,
    FindingId,
    RecommendationId,
)
from codestrata_platform.domain.intelligence.value_objects import (
    Finding,
    Metric,
    Recommendation,
)


class InMemoryAssessmentIntelligenceRepository:
    def __init__(self) -> None:
        self._items: dict[str, AssessmentIntelligence] = {}

    def get(self, intelligence_id: AssessmentIntelligenceId) -> AssessmentIntelligence | None:
        item = self._items.get(intelligence_id.value)
        return item.snapshot() if item is not None else None

    def save(self, intelligence: AssessmentIntelligence) -> None:
        self._items[intelligence.intelligence_id.value] = intelligence.snapshot()

    def find_by_idempotency_key(
        self,
        *,
        assessment_id: AssessmentId,
        idempotency_key: str,
    ) -> AssessmentIntelligence | None:
        for item in self._items.values():
            if (
                item.assessment_id == assessment_id
                and item.idempotency_key == idempotency_key
            ):
                return item.snapshot()
        return None

    def list_by_assessment(
        self,
        assessment_id: AssessmentId,
    ) -> tuple[AssessmentIntelligence, ...]:
        return tuple(
            item.snapshot()
            for item in self._items.values()
            if item.assessment_id == assessment_id
        )

    def latest_revision_for_assessment(self, assessment_id: AssessmentId) -> int:
        revisions = [
            item.revision
            for item in self._items.values()
            if item.assessment_id == assessment_id
        ]
        return max(revisions) if revisions else 0


class InMemoryFindingRepository:
    def __init__(self) -> None:
        self._items: dict[str, Finding] = {}
        self._by_assessment: dict[str, set[str]] = {}

    def get(self, finding_id: FindingId) -> Finding | None:
        return self._items.get(finding_id.value)

    def save(self, finding: Finding) -> None:
        self._items[finding.finding_id.value] = finding
        bucket = self._by_assessment.setdefault(finding.assessment_id.value, set())
        bucket.add(finding.finding_id.value)

    def list_by_assessment(self, assessment_id: AssessmentId) -> tuple[Finding, ...]:
        ids = self._by_assessment.get(assessment_id.value, set())
        return tuple(self._items[item_id] for item_id in sorted(ids) if item_id in self._items)

    def replace_for_assessment(
        self,
        assessment_id: AssessmentId,
        findings: tuple[Finding, ...],
        *,
        intelligence_id: str | None = None,
    ) -> None:
        _ = intelligence_id
        existing = self._by_assessment.get(assessment_id.value, set())
        for finding_id in existing:
            self._items.pop(finding_id, None)
        self._by_assessment[assessment_id.value] = set()
        for finding in findings:
            self.save(finding)


class InMemoryMetricRepository:
    def __init__(self) -> None:
        self._items: dict[str, Metric] = {}
        self._by_assessment: dict[str, list[str]] = {}

    def save(self, metric: Metric) -> None:
        self._items[metric.name.value] = metric

    def list_by_assessment(self, assessment_id: AssessmentId) -> tuple[Metric, ...]:
        names = self._by_assessment.get(assessment_id.value, [])
        return tuple(self._items[name] for name in names if name in self._items)

    def replace_for_assessment(
        self,
        assessment_id: AssessmentId,
        metrics: tuple[Metric, ...],
        *,
        intelligence_id: str | None = None,
    ) -> None:
        _ = intelligence_id
        for name in self._by_assessment.get(assessment_id.value, []):
            self._items.pop(name, None)
        ordered_names: list[str] = []
        for metric in metrics:
            self._items[metric.name.value] = metric
            ordered_names.append(metric.name.value)
        self._by_assessment[assessment_id.value] = ordered_names


class InMemoryRecommendationRepository:
    def __init__(self) -> None:
        self._items: dict[str, Recommendation] = {}
        self._by_assessment: dict[str, set[str]] = {}

    def get(self, recommendation_id: RecommendationId) -> Recommendation | None:
        return self._items.get(recommendation_id.value)

    def save(self, recommendation: Recommendation) -> None:
        self._items[recommendation.recommendation_id.value] = recommendation
        bucket = self._by_assessment.setdefault(recommendation.assessment_id.value, set())
        bucket.add(recommendation.recommendation_id.value)

    def list_by_assessment(
        self,
        assessment_id: AssessmentId,
    ) -> tuple[Recommendation, ...]:
        ids = self._by_assessment.get(assessment_id.value, set())
        return tuple(self._items[item_id] for item_id in sorted(ids) if item_id in self._items)

    def replace_for_assessment(
        self,
        assessment_id: AssessmentId,
        recommendations: tuple[Recommendation, ...],
        *,
        intelligence_id: str | None = None,
    ) -> None:
        _ = intelligence_id
        existing = self._by_assessment.get(assessment_id.value, set())
        for recommendation_id in existing:
            self._items.pop(recommendation_id, None)
        self._by_assessment[assessment_id.value] = set()
        for recommendation in recommendations:
            self.save(recommendation)
