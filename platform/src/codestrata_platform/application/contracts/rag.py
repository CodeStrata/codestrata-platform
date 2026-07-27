"""RagService contract (future capability)."""

from __future__ import annotations

from typing import Protocol

from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId


class RagService(Protocol):
    """Contract for Retrieval-Augmented Generation over Platform knowledge.

    No implementation in Phase 8.1.1. Never performs Engine analysis.
    """

    def index_repository(
        self,
        *,
        workspace_id: WorkspaceId,
        repository_id: RepositoryId,
    ) -> None:
        """Index repository knowledge for retrieval."""

    def answer(
        self,
        *,
        workspace_id: WorkspaceId,
        repository_id: RepositoryId,
        question: str,
    ) -> object:
        """Answer a grounded question for a repository."""
