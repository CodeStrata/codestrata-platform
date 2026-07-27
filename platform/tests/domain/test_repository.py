"""Domain tests for Repository aggregate."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from codestrata_platform.domain.errors import (
    InvalidStateTransitionError,
    InvalidValueError,
)
from codestrata_platform.domain.organization import Organization
from codestrata_platform.domain.repository import (
    Repository,
    RepositoryMetadata,
    RepositoryProvider,
    RepositorySnapshot,
    RepositoryStatus,
    RepositoryVisibility,
)
from codestrata_platform.domain.shared import CreatedAt
from codestrata_platform.domain.workspace import Workspace


def _workspace() -> Workspace:
    org = Organization.create(name="Acme")
    return Workspace.create(organization_id=org.organization_id, name="Default")


def test_repository_register_and_lifecycle() -> None:
    workspace = _workspace()
    repo = Repository.register(
        workspace_id=workspace.workspace_id,
        organization_id=workspace.organization_id,
        display_name="spring-petclinic",
        provider=RepositoryProvider.GITHUB,
        repository_url="https://github.com/example/spring-petclinic",
        default_branch="main",
        visibility=RepositoryVisibility.PRIVATE,
        description="Sample app",
    )
    assert repo.status is RepositoryStatus.ACTIVE
    repo.rename("Petclinic")
    assert repo.display_name == "Petclinic"
    repo.update_metadata({"language": "java", "tier": "critical"})
    assert repo.metadata.attributes["language"] == "java"
    repo.archive()
    assert repo.status is RepositoryStatus.ARCHIVED
    with pytest.raises(InvalidStateTransitionError):
        repo.rename("Blocked")
    with pytest.raises(InvalidStateTransitionError):
        repo.archive()


def test_repository_rejects_blank_fields() -> None:
    workspace = _workspace()
    with pytest.raises(InvalidValueError):
        Repository.register(
            workspace_id=workspace.workspace_id,
            organization_id=workspace.organization_id,
            display_name=" ",
            provider=RepositoryProvider.GITHUB,
            repository_url="https://github.com/example/app",
        )


def test_repository_metadata_and_snapshot_value_objects() -> None:
    meta = RepositoryMetadata.empty().merge({"a": "1"})
    assert meta.attributes == {"a": "1"}
    with pytest.raises(InvalidValueError):
        RepositoryMetadata({"": "x"})
    snapshot = RepositorySnapshot(
        commit_sha="abcdef1",
        captured_at=CreatedAt(datetime(2026, 7, 1, tzinfo=UTC)),
        ref_name="main",
    )
    assert snapshot.commit_sha == "abcdef1"
    with pytest.raises(InvalidValueError):
        RepositorySnapshot(
            commit_sha="xyz",
            captured_at=CreatedAt(datetime(2026, 7, 1, tzinfo=UTC)),
        )


def test_repository_id_immutability() -> None:
    workspace = _workspace()
    repo = Repository.register(
        workspace_id=workspace.workspace_id,
        organization_id=workspace.organization_id,
        display_name="app",
        provider=RepositoryProvider.OTHER,
        repository_url="https://example.com/app.git",
    )
    with pytest.raises(FrozenInstanceError):
        repo.repository_id.value = "mutated"  # type: ignore[misc]
