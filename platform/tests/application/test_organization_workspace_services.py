"""Organization and workspace application service tests."""

from __future__ import annotations

import pytest

from codestrata_platform.application.commands.organization import (
    ActivateOrganizationCommand,
    CreateOrganizationCommand,
    DeactivateOrganizationCommand,
    RenameOrganizationCommand,
)
from codestrata_platform.application.commands.workspace import (
    ActivateWorkspaceCommand,
    CreateWorkspaceCommand,
    DeactivateWorkspaceCommand,
    RenameWorkspaceCommand,
)
from codestrata_platform.application.common.errors import NotFoundError, ValidationError
from codestrata_platform.application.organization import DefaultOrganizationService
from codestrata_platform.application.queries.organization import OrganizationQuery
from codestrata_platform.application.queries.workspace import WorkspaceQuery
from codestrata_platform.application.workspace import DefaultWorkspaceService
from codestrata_platform.domain.organization import OrganizationId, OrganizationStatus
from codestrata_platform.domain.workspace import WorkspaceId, WorkspaceStatus


def test_organization_lifecycle(organization_service: DefaultOrganizationService) -> None:
    created = organization_service.create_organization(
        CreateOrganizationCommand(name="Contoso")
    )
    assert created.status is OrganizationStatus.ACTIVE

    renamed = organization_service.rename_organization(
        RenameOrganizationCommand(
            organization_id=created.organization_id,
            name="Contoso Corp",
        )
    )
    assert renamed.name == "Contoso Corp"

    deactivated = organization_service.deactivate_organization(
        DeactivateOrganizationCommand(organization_id=created.organization_id)
    )
    assert deactivated.status is OrganizationStatus.INACTIVE

    activated = organization_service.activate_organization(
        ActivateOrganizationCommand(organization_id=created.organization_id)
    )
    assert activated.status is OrganizationStatus.ACTIVE

    listed = organization_service.list_organizations(OrganizationQuery())
    assert listed.total == 1


def test_workspace_ownership_and_lifecycle(
    organization_service: DefaultOrganizationService,
    workspace_service: DefaultWorkspaceService,
) -> None:
    org = organization_service.create_organization(CreateOrganizationCommand(name="Org"))
    workspace = workspace_service.create_workspace(
        CreateWorkspaceCommand(
            organization_id=org.organization_id,
            name="Default",
            description="Main",
        )
    )
    assert workspace.organization_id == org.organization_id

    renamed = workspace_service.rename_workspace(
        RenameWorkspaceCommand(workspace_id=workspace.workspace_id, name="Renamed")
    )
    assert renamed.name == "Renamed"

    deactivated = workspace_service.deactivate_workspace(
        DeactivateWorkspaceCommand(workspace_id=workspace.workspace_id)
    )
    assert deactivated.status is WorkspaceStatus.INACTIVE

    activated = workspace_service.activate_workspace(
        ActivateWorkspaceCommand(workspace_id=workspace.workspace_id)
    )
    assert activated.status is WorkspaceStatus.ACTIVE

    listed = workspace_service.list_workspaces(
        WorkspaceQuery(organization_id=org.organization_id)
    )
    assert listed.total == 1


def test_workspace_requires_active_organization(
    organization_service: DefaultOrganizationService,
    workspace_service: DefaultWorkspaceService,
) -> None:
    org = organization_service.create_organization(CreateOrganizationCommand(name="Org"))
    organization_service.deactivate_organization(
        DeactivateOrganizationCommand(organization_id=org.organization_id)
    )
    with pytest.raises(ValidationError) as exc:
        workspace_service.create_workspace(
            CreateWorkspaceCommand(organization_id=org.organization_id, name="Blocked")
        )
    assert exc.value.reason_code == "organization_inactive"


def test_missing_org_and_workspace(
    organization_service: DefaultOrganizationService,
    workspace_service: DefaultWorkspaceService,
) -> None:
    with pytest.raises(NotFoundError):
        organization_service.get_organization(OrganizationId.generate())
    with pytest.raises(NotFoundError):
        workspace_service.get_workspace(WorkspaceId.generate())
