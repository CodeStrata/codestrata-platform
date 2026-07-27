"""SqlAlchemyOrganizationRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from codestrata_platform.domain.organization import Organization, OrganizationId
from codestrata_platform.infrastructure.persistence.mappers.organization_mapper import (
    OrganizationMapper,
)
from codestrata_platform.infrastructure.persistence.models.organization_record import (
    OrganizationRecord,
)


class SqlAlchemyOrganizationRepository:
    """Durable OrganizationRepository adapter."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, organization_id: OrganizationId) -> Organization | None:
        record = self._session.get(OrganizationRecord, organization_id.value)
        if record is None:
            return None
        return OrganizationMapper.to_domain(record)

    def save(self, organization: Organization) -> None:
        record = self._session.get(OrganizationRecord, organization.organization_id.value)
        if record is None:
            self._session.add(OrganizationMapper.to_record(organization))
        else:
            OrganizationMapper.apply_to_record(organization, record)
        self._session.flush()

    def list_all(self) -> tuple[Organization, ...]:
        records = self._session.scalars(select(OrganizationRecord)).all()
        return tuple(OrganizationMapper.to_domain(record) for record in records)
