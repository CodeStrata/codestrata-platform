"""Assessment registration commands."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from codestrata_platform.domain.assessment import (
    AssessmentId,
    AssessmentReference,
    AssessmentVersion,
    GeneratedReport,
)
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.shared.version import PlatformVersion
from codestrata_platform.domain.workspace.ids import WorkspaceId


@dataclass(frozen=True, slots=True)
class RegisterAssessmentCommand:
    repository_id: RepositoryId
    workspace_id: WorkspaceId
    engine_version: PlatformVersion | str
    assessment_version: AssessmentVersion | str
    metadata: Mapping[str, str] | None = None


@dataclass(frozen=True, slots=True)
class StartAssessmentCommand:
    assessment_id: AssessmentId


@dataclass(frozen=True, slots=True)
class CompleteAssessmentCommand:
    assessment_id: AssessmentId
    generated_reports: tuple[GeneratedReport, ...] = ()
    references: tuple[AssessmentReference, ...] = ()


@dataclass(frozen=True, slots=True)
class FailAssessmentCommand:
    assessment_id: AssessmentId
    reason: str
