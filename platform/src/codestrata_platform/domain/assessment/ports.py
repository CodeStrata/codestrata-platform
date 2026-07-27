"""Persistence port for the Assessment aggregate."""

from __future__ import annotations

from typing import Protocol

from codestrata_platform.domain.assessment.aggregate import Assessment
from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId


class AssessmentRepository(Protocol):
    """Assessment port — no persistence implementation in Phase 8.1.1."""

    def get(self, assessment_id: AssessmentId) -> Assessment | None:
        """Load an assessment by id, or None when absent."""

    def save(self, assessment: Assessment) -> None:
        """Insert or update an assessment aggregate."""

    def list_by_repository(
        self,
        repository_id: RepositoryId,
    ) -> tuple[Assessment, ...]:
        """List assessments for a repository (history)."""

    def list_by_workspace(self, workspace_id: WorkspaceId) -> tuple[Assessment, ...]:
        """List assessments within a workspace."""
