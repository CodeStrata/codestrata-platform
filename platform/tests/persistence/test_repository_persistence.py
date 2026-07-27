"""Repository rename/metadata/archive and uniqueness persistence tests."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from codestrata_platform.domain.organization import Organization
from codestrata_platform.domain.repository import Repository, RepositoryProvider, RepositoryStatus
from codestrata_platform.domain.workspace import Workspace
from codestrata_platform.infrastructure.persistence.repositories import (
    SqlAlchemyOrganizationRepository,
    SqlAlchemyRepositoryRepository,
    SqlAlchemyWorkspaceRepository,
)


def _seed(
    org_repo: SqlAlchemyOrganizationRepository,
    workspace_repo: SqlAlchemyWorkspaceRepository,
) -> tuple[Organization, Workspace]:
    org = Organization.create(name="Org")
    org_repo.save(org)
    workspace = Workspace.create(organization_id=org.organization_id, name="WS")
    workspace_repo.save(workspace)
    return org, workspace


def test_rename_and_metadata_persist(
    org_repo: SqlAlchemyOrganizationRepository,
    workspace_repo: SqlAlchemyWorkspaceRepository,
    repository_repo: SqlAlchemyRepositoryRepository,
) -> None:
    org, workspace = _seed(org_repo, workspace_repo)
    repository = Repository.register(
        workspace_id=workspace.workspace_id,
        organization_id=org.organization_id,
        display_name="App",
        provider=RepositoryProvider.GITHUB,
        repository_url="https://github.com/acme/app",
    )
    repository_repo.save(repository)

    repository.rename("App Core")
    repository.update_metadata({"owner": "platform"})
    repository_repo.save(repository)

    loaded = repository_repo.get(repository.repository_id)
    assert loaded is not None
    assert loaded.display_name == "App Core"
    assert loaded.metadata.attributes["owner"] == "platform"


def test_archive_persists(
    org_repo: SqlAlchemyOrganizationRepository,
    workspace_repo: SqlAlchemyWorkspaceRepository,
    repository_repo: SqlAlchemyRepositoryRepository,
) -> None:
    org, workspace = _seed(org_repo, workspace_repo)
    repository = Repository.register(
        workspace_id=workspace.workspace_id,
        organization_id=org.organization_id,
        display_name="App",
        provider=RepositoryProvider.GITHUB,
        repository_url="https://github.com/acme/app",
    )
    repository_repo.save(repository)
    repository.archive()
    repository_repo.save(repository)

    loaded = repository_repo.get(repository.repository_id)
    assert loaded is not None
    assert loaded.status is RepositoryStatus.ARCHIVED


def test_duplicate_active_url_rejected_at_database(
    org_repo: SqlAlchemyOrganizationRepository,
    workspace_repo: SqlAlchemyWorkspaceRepository,
    repository_repo: SqlAlchemyRepositoryRepository,
    session,
) -> None:
    org, workspace = _seed(org_repo, workspace_repo)
    first = Repository.register(
        workspace_id=workspace.workspace_id,
        organization_id=org.organization_id,
        display_name="A",
        provider=RepositoryProvider.GITHUB,
        repository_url="https://github.com/acme/app",
    )
    repository_repo.save(first)

    second = Repository.register(
        workspace_id=workspace.workspace_id,
        organization_id=org.organization_id,
        display_name="B",
        provider=RepositoryProvider.GITHUB,
        repository_url="https://github.com/acme/app/",
    )
    with pytest.raises(IntegrityError):
        repository_repo.save(second)
        session.flush()
    session.rollback()


def test_archived_url_can_be_re_registered(
    org_repo: SqlAlchemyOrganizationRepository,
    workspace_repo: SqlAlchemyWorkspaceRepository,
    repository_repo: SqlAlchemyRepositoryRepository,
) -> None:
    org, workspace = _seed(org_repo, workspace_repo)
    first = Repository.register(
        workspace_id=workspace.workspace_id,
        organization_id=org.organization_id,
        display_name="A",
        provider=RepositoryProvider.GITHUB,
        repository_url="https://github.com/acme/app",
    )
    repository_repo.save(first)
    first.archive()
    repository_repo.save(first)

    second = Repository.register(
        workspace_id=workspace.workspace_id,
        organization_id=org.organization_id,
        display_name="B",
        provider=RepositoryProvider.GITHUB,
        repository_url="https://github.com/acme/app",
    )
    repository_repo.save(second)
    assert repository_repo.get(second.repository_id) is not None


def test_foreign_key_requires_workspace(
    org_repo: SqlAlchemyOrganizationRepository,
    repository_repo: SqlAlchemyRepositoryRepository,
    session,
) -> None:
    org = Organization.create(name="Org")
    org_repo.save(org)
    from codestrata_platform.domain.workspace.ids import WorkspaceId

    orphan = Repository.register(
        workspace_id=WorkspaceId.generate(),
        organization_id=org.organization_id,
        display_name="Orphan",
        provider=RepositoryProvider.GITHUB,
        repository_url="https://github.com/acme/orphan",
    )
    with pytest.raises(IntegrityError):
        repository_repo.save(orphan)
        session.flush()
    session.rollback()
