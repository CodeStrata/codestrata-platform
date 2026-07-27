"""Port contract tests shared by in-memory and SQLAlchemy adapters."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import text

from codestrata_platform.domain.organization import Organization
from codestrata_platform.domain.repository import Repository, RepositoryProvider
from codestrata_platform.domain.workspace import Workspace
from codestrata_platform.infrastructure.memory import (
    InMemoryOrganizationRepository,
    InMemoryRepositoryRepository,
    InMemoryWorkspaceRepository,
)
from codestrata_platform.infrastructure.persistence import (
    create_engine_from_url,
    create_platform_schema,
    create_session_factory,
)
from codestrata_platform.infrastructure.persistence.repositories import (
    SqlAlchemyOrganizationRepository,
    SqlAlchemyRepositoryRepository,
    SqlAlchemyWorkspaceRepository,
)

from .postgres_support import ephemeral_postgres, try_existing_database_url


@pytest.fixture(params=["memory", "sqlalchemy"])
def adapter_stack(request, tmp_path_factory) -> Iterator[tuple]:
    if request.param == "memory":
        yield (
            InMemoryOrganizationRepository(),
            InMemoryWorkspaceRepository(),
            InMemoryRepositoryRepository(),
        )
        return

    existing = try_existing_database_url()
    ctx = None
    managed = False
    if existing is not None:
        url = existing
    else:
        ctx = ephemeral_postgres(Path(tmp_path_factory.mktemp("port-pg")))
        url = ctx.__enter__()
        managed = True
    engine = create_engine_from_url(url)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    create_platform_schema(engine)
    session = create_session_factory(engine)()
    try:
        yield (
            SqlAlchemyOrganizationRepository(session),
            SqlAlchemyWorkspaceRepository(session),
            SqlAlchemyRepositoryRepository(session),
        )
        session.commit()
    finally:
        session.close()
        engine.dispose()
        if managed and ctx is not None:
            ctx.__exit__(None, None, None)


def test_port_contract_save_get_list(adapter_stack: tuple) -> None:
    org_repo, workspace_repo, repository_repo = adapter_stack

    org = Organization.create(name="Org")
    org_repo.save(org)
    assert org_repo.get(org.organization_id) is not None
    assert len(org_repo.list_all()) == 1

    workspace = Workspace.create(organization_id=org.organization_id, name="WS")
    workspace_repo.save(workspace)
    assert workspace_repo.get(workspace.workspace_id) is not None
    assert len(workspace_repo.list_by_organization(org.organization_id)) == 1

    repository = Repository.register(
        workspace_id=workspace.workspace_id,
        organization_id=org.organization_id,
        display_name="App",
        provider=RepositoryProvider.GITHUB,
        repository_url="https://github.com/acme/app",
    )
    repository_repo.save(repository)
    assert repository_repo.get(repository.repository_id) is not None
    assert len(repository_repo.list_by_workspace(workspace.workspace_id)) == 1
    assert len(repository_repo.list_by_organization(org.organization_id)) == 1
