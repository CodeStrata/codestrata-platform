"""Assessment application models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from codestrata_platform.domain.assessment import (
    Assessment,
    AssessmentId,
    AssessmentStatus,
)
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId


@dataclass(frozen=True, slots=True)
class AssessmentSummary:
    assessment_id: AssessmentId
    repository_id: RepositoryId
    workspace_id: WorkspaceId
    engine_version: str
    assessment_version: str
    status: AssessmentStatus
    started_at: datetime | None
    completed_at: datetime | None
    failure_reason: str | None
    report_count: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_aggregate(cls, assessment: Assessment) -> AssessmentSummary:
        return cls(
            assessment_id=assessment.assessment_id,
            repository_id=assessment.repository_id,
            workspace_id=assessment.workspace_id,
            engine_version=str(assessment.engine_version),
            assessment_version=str(assessment.assessment_version),
            status=assessment.status,
            started_at=assessment.started_at,
            completed_at=assessment.completed_at,
            failure_reason=assessment.failure_reason,
            report_count=len(assessment.generated_reports),
            created_at=assessment.audit.created_at.value,
            updated_at=assessment.audit.updated_at.value,
        )
