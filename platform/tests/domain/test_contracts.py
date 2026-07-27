"""Contract import smoke tests for Phase 8.1.1 ports and services."""

from __future__ import annotations

from codestrata_platform.application.contracts import (
    AssessmentService,
    KnowledgeGraphService,
    McpService,
    OrganizationService,
    PortfolioService,
    RagService,
    RepositoryService,
    WorkspaceService,
)
from codestrata_platform.domain.assessment import AssessmentRepository
from codestrata_platform.domain.organization import OrganizationRepository
from codestrata_platform.domain.repository import RepositoryRepository
from codestrata_platform.domain.workspace import WorkspaceRepository


def test_repository_ports_and_service_contracts_are_importable() -> None:
    assert RepositoryRepository is not None
    assert AssessmentRepository is not None
    assert WorkspaceRepository is not None
    assert OrganizationRepository is not None
    assert RepositoryService is not None
    assert AssessmentService is not None
    assert WorkspaceService is not None
    assert OrganizationService is not None
    assert KnowledgeGraphService is not None
    assert RagService is not None
    assert PortfolioService is not None
    assert McpService is not None
