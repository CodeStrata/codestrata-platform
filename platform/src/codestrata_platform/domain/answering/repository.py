"""Answer run persistence ports."""

from __future__ import annotations

from typing import Protocol

from codestrata_platform.domain.answering.answer import EngineeringAnswerRun
from codestrata_platform.domain.answering.identifiers import AnswerRunId
from codestrata_platform.domain.repository.ids import RepositoryId


class AnswerRunRepository(Protocol):
    def get(self, answer_run_id: AnswerRunId) -> EngineeringAnswerRun | None: ...

    def save(self, run: EngineeringAnswerRun) -> None: ...

    def find_by_projection_key(self, projection_key: str) -> EngineeringAnswerRun | None: ...

    def list_by_repository(
        self,
        repository_id: RepositoryId,
        *,
        limit: int = 50,
    ) -> tuple[EngineeringAnswerRun, ...]: ...
