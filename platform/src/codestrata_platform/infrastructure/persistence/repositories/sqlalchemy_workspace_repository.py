"""SqlAlchemyWorkspaceRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.workspace import Workspace, WorkspaceId
from codestrata_platform.infrastructure.persistence.mappers.workspace_mapper import WorkspaceMapper
from codestrata_platform.infrastructure.persistence.models.workspace_record import WorkspaceRecord


class SqlAlchemyWorkspaceRepository:
    """Durable WorkspaceRepository adapter."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, workspace_id: WorkspaceId) -> Workspace | None:
        record = self._session.get(WorkspaceRecord, workspace_id.value)
        if record is None:
            return None
        return WorkspaceMapper.to_domain(record)

    def save(self, workspace: Workspace) -> None:
        record = self._session.get(WorkspaceRecord, workspace.workspace_id.value)
        if record is None:
            self._session.add(WorkspaceMapper.to_record(workspace))
        else:
            WorkspaceMapper.apply_to_record(workspace, record)
        self._session.flush()

    def list_by_organization(self, organization_id: OrganizationId) -> tuple[Workspace, ...]:
        records = self._session.scalars(
            select(WorkspaceRecord).where(WorkspaceRecord.organization_id == organization_id.value)
        ).all()
        return tuple(WorkspaceMapper.to_domain(record) for record in records)
