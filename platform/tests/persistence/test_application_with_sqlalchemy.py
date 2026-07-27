"""Application workflows exercised against SQLAlchemy adapters."""

from __future__ import annotations

import pytest

from codestrata_platform.application.assessment import DefaultAssessmentService
from codestrata_platform.application.commands.assessment import RegisterAssessmentCommand
from codestrata_platform.application.commands.organization import CreateOrganizationCommand
from codestrata_platform.application.commands.repository import (
    ArchiveRepositoryCommand,
    RegisterRepositoryCommand,
    RenameRepositoryCommand,
)
from codestrata_platform.application.commands.workspace import CreateWorkspaceCommand
from codestrata_platform.application.common.errors import ConflictError
from codestrata_platform.application.common.pagination import PageRequest
from codestrata_platform.application.organization import DefaultOrganizationService
from codestrata_platform.application.queries.repository import RepositoryQuery
from codestrata_platform.application.repository import DefaultRepositoryService
from codestrata_platform.application.workspace import DefaultWorkspaceService
from codestrata_platform.domain.repository import RepositoryProvider, RepositoryStatus
from codestrata_platform.infrastructure.persistence import SqlAlchemyUnitOfWork


def test_registry_workflow_and_pagination(session_factory) -> None:
    with SqlAlchemyUnitOfWork(session_factory) as uow:
        assert uow.organizations and uow.workspaces and uow.repositories and uow.assessments
        org_service = DefaultOrganizationService(organizations=uow.organizations)
        workspace_service = DefaultWorkspaceService(
            workspaces=uow.workspaces,
            organizations=uow.organizations,
        )
        repository_service = DefaultRepositoryService(
            repositories=uow.repositories,
            workspaces=uow.workspaces,
            organizations=uow.organizations,
        )
        assessment_service = DefaultAssessmentService(
            assessments=uow.assessments,
            repositories=uow.repositories,
            workspaces=uow.workspaces,
        )

        org = org_service.create_organization(CreateOrganizationCommand(name="Acme"))
        workspace = workspace_service.create_workspace(
            CreateWorkspaceCommand(organization_id=org.organization_id, name="Eng")
        )

        for index in range(3):
            repository_service.register_repository(
                RegisterRepositoryCommand(
                    workspace_id=workspace.workspace_id,
                    organization_id=org.organization_id,
                    display_name=f"App {index}",
                    provider=RepositoryProvider.GITHUB,
                    repository_url=f"https://github.com/acme/app-{index}",
                )
            )

        page = repository_service.list_repositories(
            RepositoryQuery(
                workspace_id=workspace.workspace_id,
                page=PageRequest(offset=1, limit=1),
            )
        )
        assert page.total == 3
        assert len(page.items) == 1
        assert page.has_more is True

        first = repository_service.list_repositories(
            RepositoryQuery(workspace_id=workspace.workspace_id)
        ).items[0]
        renamed = repository_service.rename_repository(
            RenameRepositoryCommand(repository_id=first.repository_id, display_name="Renamed")
        )
        assert renamed.display_name == "Renamed"

        with pytest.raises(ConflictError):
            repository_service.register_repository(
                RegisterRepositoryCommand(
                    workspace_id=workspace.workspace_id,
                    organization_id=org.organization_id,
                    display_name="Dup",
                    provider=RepositoryProvider.GITHUB,
                    repository_url=first.repository_url + "/",
                )
            )

        assessment_service.create_assessment(
            RegisterAssessmentCommand(
                repository_id=first.repository_id,
                workspace_id=workspace.workspace_id,
                engine_version="1.0.0",
                assessment_version="0.1.0",
            )
        )
        history = assessment_service.list_assessment_history(first.repository_id)
        assert len(history) == 1

        archived = repository_service.archive_repository(
            ArchiveRepositoryCommand(repository_id=first.repository_id)
        )
        assert archived.status is RepositoryStatus.ARCHIVED
        uow.commit()
