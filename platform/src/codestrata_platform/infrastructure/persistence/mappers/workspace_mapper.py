"""Workspace aggregate ↔ WorkspaceRecord mapper."""

from __future__ import annotations

from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.workspace import Workspace, WorkspaceId, WorkspaceStatus
from codestrata_platform.infrastructure.persistence.mappers._helpers import audit_from_record
from codestrata_platform.infrastructure.persistence.models.workspace_record import WorkspaceRecord


class WorkspaceMapper:
    @staticmethod
    def to_record(workspace: Workspace) -> WorkspaceRecord:
        return WorkspaceRecord(
            id=workspace.workspace_id.value,
            organization_id=workspace.organization_id.value,
            name=workspace.name,
            description=workspace.description,
            status=workspace.status.value,
            created_at=workspace.audit.created_at.value,
            updated_at=workspace.audit.updated_at.value,
            version=workspace._version,
        )

    @staticmethod
    def apply_to_record(workspace: Workspace, record: WorkspaceRecord) -> None:
        record.organization_id = workspace.organization_id.value
        record.name = workspace.name
        record.description = workspace.description
        record.status = workspace.status.value
        record.created_at = workspace.audit.created_at.value
        record.updated_at = workspace.audit.updated_at.value
        record.version = workspace._version

    @staticmethod
    def to_domain(record: WorkspaceRecord) -> Workspace:
        return Workspace(
            workspace_id=WorkspaceId(record.id),
            organization_id=OrganizationId(record.organization_id),
            name=record.name,
            description=record.description,
            status=WorkspaceStatus(record.status),
            audit=audit_from_record(
                created_at=record.created_at,
                updated_at=record.updated_at,
            ),
            _version=record.version,
        )
