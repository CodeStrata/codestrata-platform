"""In-memory answer run repository."""

from __future__ import annotations

from codestrata_platform.domain.answering.answer import EngineeringAnswerRun
from codestrata_platform.domain.answering.identifiers import AnswerRunId
from codestrata_platform.domain.answering.lifecycle import AnswerStatus
from codestrata_platform.domain.repository.ids import RepositoryId


class InMemoryAnswerRunRepository:
    def __init__(self) -> None:
        self._items: dict[str, EngineeringAnswerRun] = {}

    def get(self, answer_run_id: AnswerRunId) -> EngineeringAnswerRun | None:
        item = self._items.get(answer_run_id.value)
        return item.snapshot() if item is not None else None

    def save(self, run: EngineeringAnswerRun) -> None:
        self._items[run.answer_run_id.value] = run.snapshot()

    def find_by_projection_key(self, projection_key: str) -> EngineeringAnswerRun | None:
        key = projection_key.strip()
        matches = [
            item
            for item in self._items.values()
            if item.projection_key.value == key and item.status is AnswerStatus.COMPLETED
        ]
        if not matches:
            return None
        return matches[-1].snapshot()

    def list_by_repository(
        self,
        repository_id: RepositoryId,
        *,
        limit: int = 50,
    ) -> tuple[EngineeringAnswerRun, ...]:
        items = [
            item.snapshot()
            for item in self._items.values()
            if item.repository_id == repository_id
        ]
        items.sort(key=lambda item: item.audit.created_at.value, reverse=True)
        return tuple(items[: max(1, limit)])
