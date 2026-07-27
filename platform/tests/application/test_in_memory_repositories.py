"""In-memory repository adapter tests."""

from __future__ import annotations

from codestrata_platform.domain.organization import Organization
from codestrata_platform.domain.repository import Repository, RepositoryProvider
from codestrata_platform.domain.workspace import Workspace
from codestrata_platform.infrastructure.memory import (
    InMemoryOrganizationRepository,
    InMemoryRepositoryRepository,
    InMemoryWorkspaceRepository,
)


def test_in_memory_round_trip_and_isolation() -> None:
    orgs = InMemoryOrganizationRepository()
    workspaces = InMemoryWorkspaceRepository()
    repositories = InMemoryRepositoryRepository()

    org = Organization.create(name="Org")
    orgs.save(org)

    workspace = Workspace.create(organization_id=org.organization_id, name="WS")
    workspaces.save(workspace)

    repository = Repository.register(
        workspace_id=workspace.workspace_id,
        organization_id=org.organization_id,
        display_name="App",
        provider=RepositoryProvider.GITHUB,
        repository_url="https://github.com/acme/app",
    )
    repositories.save(repository)

    loaded = repositories.get(repository.repository_id)
    assert loaded is not None
    loaded.rename("Mutated")
    # Mutation of a loaded snapshot must not affect the store until save.
    untouched = repositories.get(repository.repository_id)
    assert untouched is not None
    assert untouched.display_name == "App"

    repositories.save(loaded)
    saved = repositories.get(repository.repository_id)
    assert saved is not None
    assert saved.display_name == "Mutated"

    assert len(repositories.list_by_workspace(workspace.workspace_id)) == 1
    assert len(workspaces.list_by_organization(org.organization_id)) == 1
    assert len(orgs.list_all()) == 1
