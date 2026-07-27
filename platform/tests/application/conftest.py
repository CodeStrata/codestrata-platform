"""Shared fixtures for Commercial Platform application tests."""

from __future__ import annotations

import pytest

from codestrata_platform.application.assessment import DefaultAssessmentService
from codestrata_platform.application.commands.organization import CreateOrganizationCommand
from codestrata_platform.application.commands.workspace import CreateWorkspaceCommand
from codestrata_platform.application.organization import DefaultOrganizationService
from codestrata_platform.application.repository import DefaultRepositoryService
from codestrata_platform.application.workspace import DefaultWorkspaceService
from codestrata_platform.infrastructure.memory import (
    InMemoryAssessmentRepository,
    InMemoryOrganizationRepository,
    InMemoryRepositoryRepository,
    InMemoryWorkspaceRepository,
)


@pytest.fixture
def org_store() -> InMemoryOrganizationRepository:
    return InMemoryOrganizationRepository()


@pytest.fixture
def workspace_store() -> InMemoryWorkspaceRepository:
    return InMemoryWorkspaceRepository()


@pytest.fixture
def repository_store() -> InMemoryRepositoryRepository:
    return InMemoryRepositoryRepository()


@pytest.fixture
def assessment_store() -> InMemoryAssessmentRepository:
    return InMemoryAssessmentRepository()


@pytest.fixture
def organization_service(
    org_store: InMemoryOrganizationRepository,
) -> DefaultOrganizationService:
    return DefaultOrganizationService(organizations=org_store)


@pytest.fixture
def workspace_service(
    workspace_store: InMemoryWorkspaceRepository,
    org_store: InMemoryOrganizationRepository,
) -> DefaultWorkspaceService:
    return DefaultWorkspaceService(workspaces=workspace_store, organizations=org_store)


@pytest.fixture
def repository_service(
    repository_store: InMemoryRepositoryRepository,
    workspace_store: InMemoryWorkspaceRepository,
    org_store: InMemoryOrganizationRepository,
) -> DefaultRepositoryService:
    return DefaultRepositoryService(
        repositories=repository_store,
        workspaces=workspace_store,
        organizations=org_store,
    )


@pytest.fixture
def assessment_service(
    assessment_store: InMemoryAssessmentRepository,
    repository_store: InMemoryRepositoryRepository,
    workspace_store: InMemoryWorkspaceRepository,
) -> DefaultAssessmentService:
    return DefaultAssessmentService(
        assessments=assessment_store,
        repositories=repository_store,
        workspaces=workspace_store,
    )


@pytest.fixture
def seeded_workspace(
    organization_service: DefaultOrganizationService,
    workspace_service: DefaultWorkspaceService,
) -> tuple:
    org = organization_service.create_organization(CreateOrganizationCommand(name="Acme"))
    workspace = workspace_service.create_workspace(
        CreateWorkspaceCommand(
            organization_id=org.organization_id,
            name="Engineering",
            description="Primary workspace",
        )
    )
    return org, workspace
