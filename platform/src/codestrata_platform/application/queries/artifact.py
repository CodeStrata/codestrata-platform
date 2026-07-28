"""Artifact application queries."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.artifact import AssessmentArtifactId
from codestrata_platform.domain.assessment.ids import AssessmentId


@dataclass(frozen=True, slots=True)
class GetArtifactQuery:
    artifact_id: AssessmentArtifactId
    assessment_id: AssessmentId


@dataclass(frozen=True, slots=True)
class ListAssessmentArtifactsQuery:
    assessment_id: AssessmentId
