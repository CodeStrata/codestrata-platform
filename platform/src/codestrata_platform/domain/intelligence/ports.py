"""Ports for assessment intelligence persistence and artifact access."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from codestrata_platform.domain.artifact.enums import ArtifactType
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


@dataclass(frozen=True, slots=True)
class CompletedArtifactContent:
    artifact_id: str
    artifact_type: ArtifactType
    schema_version: str
    checksum: str
    content: bytes


class AssessmentIntelligenceRepository(Protocol):
    def get(self, intelligence_id: AssessmentIntelligenceId) -> AssessmentIntelligence | None: ...

    def save(self, intelligence: AssessmentIntelligence) -> None: ...

    def find_by_idempotency_key(
        self,
        *,
        assessment_id: AssessmentId,
        idempotency_key: str,
    ) -> AssessmentIntelligence | None: ...

    def list_by_assessment(
        self,
        assessment_id: AssessmentId,
    ) -> tuple[AssessmentIntelligence, ...]: ...

    def latest_revision_for_assessment(self, assessment_id: AssessmentId) -> int: ...


class FindingRepository(Protocol):
    def list_by_assessment(self, assessment_id: AssessmentId) -> tuple[Finding, ...]: ...

    def get(self, finding_id: FindingId) -> Finding | None: ...


class MetricRepository(Protocol):
    def list_by_assessment(self, assessment_id: AssessmentId) -> tuple[Metric, ...]: ...


class RecommendationRepository(Protocol):
    def list_by_assessment(
        self,
        assessment_id: AssessmentId,
    ) -> tuple[Recommendation, ...]: ...

    def get(self, recommendation_id: RecommendationId) -> Recommendation | None: ...


class AssessmentArtifactReader(Protocol):
    def get_completed_artifacts_for_assessment(
        self,
        assessment_id: AssessmentId,
        *,
        artifact_ids: tuple[str, ...] | None = None,
    ) -> tuple[CompletedArtifactContent, ...]: ...
