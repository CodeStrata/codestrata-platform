"""Repository Registry application workflow tests."""

from __future__ import annotations

import pytest

from codestrata_platform.application.commands.organization import (
    CreateOrganizationCommand,
    DeactivateOrganizationCommand,
)
from codestrata_platform.application.commands.repository import (
    ArchiveRepositoryCommand,
    RegisterRepositoryCommand,
    RenameRepositoryCommand,
    UpdateRepositoryMetadataCommand,
)
from codestrata_platform.application.commands.workspace import (
    CreateWorkspaceCommand,
    DeactivateWorkspaceCommand,
)
from codestrata_platform.application.common.errors import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from codestrata_platform.application.common.pagination import PageRequest
from codestrata_platform.application.organization import DefaultOrganizationService
from codestrata_platform.application.queries.repository import RepositoryQuery
from codestrata_platform.application.repository import DefaultRepositoryService
from codestrata_platform.application.workspace import DefaultWorkspaceService
from codestrata_platform.domain.errors import InvalidStateTransitionError
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository import (
    RepositoryId,
    RepositoryProvider,
    RepositoryStatus,
    RepositoryVisibility,
)
from codestrata_platform.domain.workspace.ids import WorkspaceId


def _register_cmd(
    *,
    org_id: OrganizationId,
    workspace_id: WorkspaceId,
    url: str = "https://github.com/acme/petclinic",
    name: str = "Petclinic",
) -> RegisterRepositoryCommand:
    return RegisterRepositoryCommand(
        workspace_id=workspace_id,
        organization_id=org_id,
        display_name=name,
        provider=RepositoryProvider.GITHUB,
        repository_url=url,
        default_branch="main",
        visibility=RepositoryVisibility.PRIVATE,
        description="Sample app",
        metadata={"tier": "critical"},
    )


def test_register_retrieve_rename_archive_list(
    repository_service: DefaultRepositoryService,
    seeded_workspace: tuple,
) -> None:
    org, workspace = seeded_workspace

    details = repository_service.register_repository(
        _register_cmd(org_id=org.organization_id, workspace_id=workspace.workspace_id)
    )
    assert details.status is RepositoryStatus.ACTIVE
    assert details.metadata["tier"] == "critical"
    assert details.display_name == "Petclinic"

    fetched = repository_service.get_repository(details.repository_id)
    assert fetched.repository_id == details.repository_id
    assert fetched.repository_url == "https://github.com/acme/petclinic"

    renamed = repository_service.rename_repository(
        RenameRepositoryCommand(
            repository_id=details.repository_id,
            display_name="Petclinic Core",
        )
    )
    assert renamed.display_name == "Petclinic Core"

    updated = repository_service.update_repository_metadata(
        UpdateRepositoryMetadataCommand(
            repository_id=details.repository_id,
            updates={"owner": "platform-team"},
        )
    )
    assert updated.metadata["tier"] == "critical"
    assert updated.metadata["owner"] == "platform-team"

    listed = repository_service.list_repositories(
        RepositoryQuery(workspace_id=workspace.workspace_id)
    )
    assert listed.total == 1
    assert listed.items[0].display_name == "Petclinic Core"

    archived = repository_service.archive_repository(
        ArchiveRepositoryCommand(repository_id=details.repository_id)
    )
    assert archived.status is RepositoryStatus.ARCHIVED

    active_only = repository_service.list_repositories(
        RepositoryQuery(
            workspace_id=workspace.workspace_id,
            status=RepositoryStatus.ACTIVE,
        )
    )
    assert active_only.total == 0


def test_duplicate_repository_url_rejected(
    repository_service: DefaultRepositoryService,
    seeded_workspace: tuple,
) -> None:
    org, workspace = seeded_workspace
    cmd = _register_cmd(org_id=org.organization_id, workspace_id=workspace.workspace_id)
    repository_service.register_repository(cmd)

    with pytest.raises(ConflictError) as exc:
        repository_service.register_repository(
            _register_cmd(
                org_id=org.organization_id,
                workspace_id=workspace.workspace_id,
                url="https://github.com/acme/petclinic/",
                name="Duplicate",
            )
        )
    assert exc.value.reason_code == "duplicate_repository_url"


def test_archived_url_can_be_re_registered(
    repository_service: DefaultRepositoryService,
    seeded_workspace: tuple,
) -> None:
    org, workspace = seeded_workspace
    first = repository_service.register_repository(
        _register_cmd(org_id=org.organization_id, workspace_id=workspace.workspace_id)
    )
    repository_service.archive_repository(
        ArchiveRepositoryCommand(repository_id=first.repository_id)
    )
    second = repository_service.register_repository(
        _register_cmd(
            org_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            name="Petclinic Revival",
        )
    )
    assert second.repository_id != first.repository_id
    assert second.status is RepositoryStatus.ACTIVE


def test_workspace_organization_mismatch(
    repository_service: DefaultRepositoryService,
    organization_service: DefaultOrganizationService,
    workspace_service: DefaultWorkspaceService,
) -> None:
    org_a = organization_service.create_organization(CreateOrganizationCommand(name="A"))
    org_b = organization_service.create_organization(CreateOrganizationCommand(name="B"))
    workspace = workspace_service.create_workspace(
        CreateWorkspaceCommand(organization_id=org_a.organization_id, name="WS")
    )

    with pytest.raises(ValidationError) as exc:
        repository_service.register_repository(
            _register_cmd(
                org_id=org_b.organization_id,
                workspace_id=workspace.workspace_id,
            )
        )
    assert exc.value.reason_code == "workspace_organization_mismatch"


def test_inactive_workspace_blocks_registration(
    repository_service: DefaultRepositoryService,
    workspace_service: DefaultWorkspaceService,
    seeded_workspace: tuple,
) -> None:
    org, workspace = seeded_workspace
    workspace_service.deactivate_workspace(
        DeactivateWorkspaceCommand(workspace_id=workspace.workspace_id)
    )
    with pytest.raises(ValidationError) as exc:
        repository_service.register_repository(
            _register_cmd(org_id=org.organization_id, workspace_id=workspace.workspace_id)
        )
    assert exc.value.reason_code == "workspace_inactive"


def test_inactive_organization_blocks_registration(
    repository_service: DefaultRepositoryService,
    organization_service: DefaultOrganizationService,
    seeded_workspace: tuple,
) -> None:
    org, workspace = seeded_workspace
    organization_service.deactivate_organization(
        DeactivateOrganizationCommand(organization_id=org.organization_id)
    )
    with pytest.raises(ValidationError) as exc:
        repository_service.register_repository(
            _register_cmd(org_id=org.organization_id, workspace_id=workspace.workspace_id)
        )
    assert exc.value.reason_code == "organization_inactive"


def test_missing_repository_raises(
    repository_service: DefaultRepositoryService,
) -> None:
    with pytest.raises(NotFoundError):
        repository_service.get_repository(RepositoryId.generate())


def test_archive_twice_raises_domain_error(
    repository_service: DefaultRepositoryService,
    seeded_workspace: tuple,
) -> None:
    org, workspace = seeded_workspace
    details = repository_service.register_repository(
        _register_cmd(org_id=org.organization_id, workspace_id=workspace.workspace_id)
    )
    repository_service.archive_repository(
        ArchiveRepositoryCommand(repository_id=details.repository_id)
    )
    with pytest.raises(InvalidStateTransitionError):
        repository_service.archive_repository(
            ArchiveRepositoryCommand(repository_id=details.repository_id)
        )


def test_list_requires_scope(repository_service: DefaultRepositoryService) -> None:
    with pytest.raises(ValidationError) as exc:
        repository_service.list_repositories(RepositoryQuery())
    assert exc.value.reason_code == "repository_query_scope_required"


def test_list_pagination(
    repository_service: DefaultRepositoryService,
    seeded_workspace: tuple,
) -> None:
    org, workspace = seeded_workspace
    for index in range(3):
        repository_service.register_repository(
            _register_cmd(
                org_id=org.organization_id,
                workspace_id=workspace.workspace_id,
                url=f"https://github.com/acme/app-{index}",
                name=f"App {index}",
            )
        )
    page = repository_service.list_repositories(
        RepositoryQuery(
            organization_id=org.organization_id,
            page=PageRequest(offset=1, limit=1),
        )
    )
    assert page.total == 3
    assert len(page.items) == 1
    assert page.has_more is True
