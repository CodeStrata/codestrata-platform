"""Domain tests for Organization and Workspace aggregates."""

from __future__ import annotations

import pytest

from codestrata_platform.domain.errors import (
    InvalidStateTransitionError,
    InvalidValueError,
)
from codestrata_platform.domain.organization import Organization, OrganizationStatus
from codestrata_platform.domain.workspace import Workspace, WorkspaceStatus


def test_organization_lifecycle() -> None:
    org = Organization.create(name="Acme Engineering")
    assert org.status is OrganizationStatus.ACTIVE
    org.rename("Acme Platform")
    assert org.name == "Acme Platform"
    org.deactivate()
    assert org.status is OrganizationStatus.INACTIVE
    with pytest.raises(InvalidStateTransitionError):
        org.rename("Nope")
    with pytest.raises(InvalidStateTransitionError):
        org.deactivate()
    org.activate()
    assert org.status is OrganizationStatus.ACTIVE
    with pytest.raises(InvalidStateTransitionError):
        org.activate()


def test_organization_rejects_blank_name() -> None:
    with pytest.raises(InvalidValueError):
        Organization.create(name="  ")


def test_workspace_lifecycle_under_organization() -> None:
    org = Organization.create(name="Acme")
    workspace = Workspace.create(
        organization_id=org.organization_id,
        name="Production",
        description="Primary customer workspace",
    )
    assert workspace.status is WorkspaceStatus.ACTIVE
    assert workspace.organization_id == org.organization_id
    workspace.rename("Prod")
    workspace.deactivate()
    with pytest.raises(InvalidStateTransitionError):
        workspace.rename("Blocked")
    workspace.activate()
    assert workspace.status is WorkspaceStatus.ACTIVE


def test_workspace_id_equality() -> None:
    org = Organization.create(name="Acme")
    workspace = Workspace.create(organization_id=org.organization_id, name="A")
    assert workspace.workspace_id == workspace.workspace_id
    assert hash(workspace.workspace_id) == hash(workspace.workspace_id)
