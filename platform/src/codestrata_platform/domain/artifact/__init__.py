"""Assessment artifact aggregate for Platform ingestion."""

from __future__ import annotations

from codestrata_platform.domain.artifact.aggregate import AssessmentArtifact
from codestrata_platform.domain.artifact.enums import ArtifactFormat, ArtifactStatus, ArtifactType
from codestrata_platform.domain.artifact.ids import AssessmentArtifactId
from codestrata_platform.domain.artifact.ports import ArtifactRepository, ArtifactStorage
from codestrata_platform.domain.artifact.value_objects import (
    ArtifactChecksum,
    ArtifactMetadata,
    ArtifactReference,
    ArtifactSize,
    ArtifactVersion,
)

__all__ = [
    "AssessmentArtifact",
    "AssessmentArtifactId",
    "ArtifactChecksum",
    "ArtifactFormat",
    "ArtifactMetadata",
    "ArtifactReference",
    "ArtifactRepository",
    "ArtifactSize",
    "ArtifactStatus",
    "ArtifactStorage",
    "ArtifactType",
    "ArtifactVersion",
]
