"""In-memory AssessmentRepository."""

from __future__ import annotations

from codestrata_platform.domain.assessment import Assessment, AssessmentId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId


class InMemoryAssessmentRepository:
    """Temporary store for Assessment aggregates."""

    def __init__(self) -> None:
        self._items: dict[str, Assessment] = {}

    def get(self, assessment_id: AssessmentId) -> Assessment | None:
        item = self._items.get(assessment_id.value)
        return item.snapshot() if item is not None else None

    def save(self, assessment: Assessment) -> None:
        self._items[assessment.assessment_id.value] = assessment.snapshot()

    def list_by_repository(self, repository_id: RepositoryId) -> tuple[Assessment, ...]:
        return tuple(
            item.snapshot()
            for item in self._items.values()
            if item.repository_id == repository_id
        )

    def list_by_workspace(self, workspace_id: WorkspaceId) -> tuple[Assessment, ...]:
        return tuple(
            item.snapshot()
            for item in self._items.values()
            if item.workspace_id == workspace_id
        )
