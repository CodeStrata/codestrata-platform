"""Artifact application commands."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from codestrata_platform.domain.artifact import (
    ArtifactFormat,
    ArtifactType,
    AssessmentArtifactId,
)
from codestrata_platform.domain.assessment.ids import AssessmentId


@dataclass(frozen=True, slots=True)
class RegisterArtifactCommand:
    assessment_id: AssessmentId
    engine_assessment_id: str
    artifact_type: ArtifactType
    format: ArtifactFormat
    schema_version: str
    checksum: str
    size_bytes: int
    metadata: Mapping[str, str] | None = None


@dataclass(frozen=True, slots=True)
class UploadArtifactCommand:
    artifact_id: AssessmentArtifactId
    assessment_id: AssessmentId
    content: bytes
    declared_checksum: str


@dataclass(frozen=True, slots=True)
class CompleteArtifactCommand:
    artifact_id: AssessmentArtifactId
    assessment_id: AssessmentId


@dataclass(frozen=True, slots=True)
class FailArtifactCommand:
    artifact_id: AssessmentArtifactId
    assessment_id: AssessmentId
    reason: str
