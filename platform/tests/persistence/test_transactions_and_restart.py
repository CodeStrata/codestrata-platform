"""Transaction rollback and PostgreSQL restart durability."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from codestrata_platform.application.assessment import DefaultAssessmentService
from codestrata_platform.application.commands.assessment import (
    CompleteAssessmentCommand,
    RegisterAssessmentCommand,
    StartAssessmentCommand,
)
from codestrata_platform.application.commands.organization import CreateOrganizationCommand
from codestrata_platform.application.commands.repository import (
    RegisterRepositoryCommand,
    RenameRepositoryCommand,
    UpdateRepositoryMetadataCommand,
)
from codestrata_platform.application.commands.workspace import CreateWorkspaceCommand
from codestrata_platform.application.organization import DefaultOrganizationService
from codestrata_platform.application.repository import DefaultRepositoryService
from codestrata_platform.application.workspace import DefaultWorkspaceService
from codestrata_platform.domain.organization import Organization
from codestrata_platform.domain.repository import RepositoryProvider, RepositoryVisibility
from codestrata_platform.domain.workspace import Workspace
from codestrata_platform.infrastructure.persistence import (
    SqlAlchemyUnitOfWork,
    create_engine_from_url,
    create_session_factory,
)


def test_unit_of_work_rollback(session_factory) -> None:
    with SqlAlchemyUnitOfWork(session_factory) as uow:
        assert uow.organizations is not None
        org = Organization.create(name="Temp")
        uow.organizations.save(org)
        uow.rollback()

    with SqlAlchemyUnitOfWork(session_factory) as uow:
        assert uow.organizations is not None
        assert uow.organizations.get(org.organization_id) is None


def test_unit_of_work_commit(session_factory) -> None:
    with SqlAlchemyUnitOfWork(session_factory) as uow:
        assert uow.organizations is not None
        org = Organization.create(name="Committed")
        uow.organizations.save(org)
        uow.commit()

    with SqlAlchemyUnitOfWork(session_factory) as uow:
        assert uow.organizations is not None
        loaded = uow.organizations.get(org.organization_id)
        assert loaded is not None
        assert loaded.name == "Committed"


def test_postgres_survives_engine_restart(postgres_engine) -> None:
    url = postgres_engine.url.render_as_string(hide_password=False)
    factory = create_session_factory(postgres_engine)

    with SqlAlchemyUnitOfWork(factory) as uow:
        assert uow.organizations is not None
        assert uow.workspaces is not None
        assert uow.repositories is not None
        assert uow.assessments is not None

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
        repository = repository_service.register_repository(
            RegisterRepositoryCommand(
                workspace_id=workspace.workspace_id,
                organization_id=org.organization_id,
                display_name="Petclinic",
                provider=RepositoryProvider.GITHUB,
                repository_url="https://github.com/acme/petclinic",
                visibility=RepositoryVisibility.PRIVATE,
                metadata={"tier": "critical"},
            )
        )
        repository = repository_service.rename_repository(
            RenameRepositoryCommand(
                repository_id=repository.repository_id,
                display_name="Petclinic Core",
            )
        )
        repository = repository_service.update_repository_metadata(
            UpdateRepositoryMetadataCommand(
                repository_id=repository.repository_id,
                updates={"owner": "platform"},
            )
        )
        assessment = assessment_service.create_assessment(
            RegisterAssessmentCommand(
                repository_id=repository.repository_id,
                workspace_id=workspace.workspace_id,
                engine_version="1.2.3",
                assessment_version="0.1.0",
            )
        )
        assessment_service.start_assessment(
            StartAssessmentCommand(assessment_id=assessment.assessment_id)
        )
        assessment = assessment_service.complete_assessment(
            CompleteAssessmentCommand(assessment_id=assessment.assessment_id)
        )
        uow.commit()

        org_id = org.organization_id
        workspace_id = workspace.workspace_id
        repository_id = repository.repository_id
        assessment_id = assessment.assessment_id

    postgres_engine.dispose()

    engine2 = create_engine_from_url(url)
    factory2 = create_session_factory(engine2)
    with SqlAlchemyUnitOfWork(factory2) as uow:
        assert uow.organizations is not None
        assert uow.workspaces is not None
        assert uow.repositories is not None
        assert uow.assessments is not None

        loaded_org = uow.organizations.get(org_id)
        loaded_ws = uow.workspaces.get(workspace_id)
        loaded_repo = uow.repositories.get(repository_id)
        loaded_assessment = uow.assessments.get(assessment_id)

        assert loaded_org is not None and loaded_org.name == "Acme"
        assert loaded_ws is not None and loaded_ws.name == "Eng"
        assert loaded_repo is not None
        assert loaded_repo.display_name == "Petclinic Core"
        assert loaded_repo.metadata.attributes["tier"] == "critical"
        assert loaded_repo.metadata.attributes["owner"] == "platform"
        assert loaded_assessment is not None
        assert loaded_assessment.status.value == "succeeded"
        assert str(loaded_assessment.engine_version) == "1.2.3"

    engine2.dispose()


def test_workspace_requires_organization_fk(session_factory) -> None:
    with SqlAlchemyUnitOfWork(session_factory) as uow:
        assert uow.workspaces is not None
        from codestrata_platform.domain.organization.ids import OrganizationId

        orphan = Workspace.create(organization_id=OrganizationId.generate(), name="Orphan")
        with pytest.raises(IntegrityError):
            uow.workspaces.save(orphan)
        uow.rollback()
