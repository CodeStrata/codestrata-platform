"""KnowledgeGraphService contract (future capability)."""

from __future__ import annotations

from typing import Protocol

from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId


class KnowledgeGraphService(Protocol):
    """Contract for Engineering Knowledge Graph capabilities.

    No implementation in Phase 8.1.1.
    """

    def build_repository_graph(
        self,
        *,
        organization_id: OrganizationId,
        workspace_id: WorkspaceId,
        repository_id: RepositoryId,
    ) -> None:
        """Build or refresh a repository knowledge graph projection."""

    def query_repository_graph(
        self,
        *,
        repository_id: RepositoryId,
        query: str,
    ) -> object:
        """Query a repository knowledge graph."""
