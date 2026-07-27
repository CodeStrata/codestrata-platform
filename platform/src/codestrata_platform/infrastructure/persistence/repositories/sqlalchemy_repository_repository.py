"""SqlAlchemyRepositoryRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository import Repository, RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.infrastructure.persistence.mappers.repository_mapper import (
    RepositoryMapper,
)
from codestrata_platform.infrastructure.persistence.models.repository_record import (
    RepositoryRecord,
)


class SqlAlchemyRepositoryRepository:
    """Durable RepositoryRepository adapter."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, repository_id: RepositoryId) -> Repository | None:
        record = self._session.get(RepositoryRecord, repository_id.value)
        if record is None:
            return None
        return RepositoryMapper.to_domain(record)

    def save(self, repository: Repository) -> None:
        record = self._session.get(RepositoryRecord, repository.repository_id.value)
        if record is None:
            self._session.add(RepositoryMapper.to_record(repository))
        else:
            RepositoryMapper.apply_to_record(repository, record)
        self._session.flush()

    def list_by_workspace(self, workspace_id: WorkspaceId) -> tuple[Repository, ...]:
        records = self._session.scalars(
            select(RepositoryRecord).where(RepositoryRecord.workspace_id == workspace_id.value)
        ).all()
        return tuple(RepositoryMapper.to_domain(record) for record in records)

    def list_by_organization(self, organization_id: OrganizationId) -> tuple[Repository, ...]:
        records = self._session.scalars(
            select(RepositoryRecord).where(
                RepositoryRecord.organization_id == organization_id.value
            )
        ).all()
        return tuple(RepositoryMapper.to_domain(record) for record in records)
