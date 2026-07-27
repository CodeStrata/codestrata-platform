"""Organization aggregate ↔ OrganizationRecord mapper."""

from __future__ import annotations

from codestrata_platform.domain.organization import Organization, OrganizationId, OrganizationStatus
from codestrata_platform.infrastructure.persistence.mappers._helpers import audit_from_record
from codestrata_platform.infrastructure.persistence.models.organization_record import (
    OrganizationRecord,
)


class OrganizationMapper:
    @staticmethod
    def to_record(organization: Organization) -> OrganizationRecord:
        return OrganizationRecord(
            id=organization.organization_id.value,
            name=organization.name,
            status=organization.status.value,
            created_at=organization.audit.created_at.value,
            updated_at=organization.audit.updated_at.value,
            version=organization._version,
        )

    @staticmethod
    def apply_to_record(organization: Organization, record: OrganizationRecord) -> None:
        record.name = organization.name
        record.status = organization.status.value
        record.created_at = organization.audit.created_at.value
        record.updated_at = organization.audit.updated_at.value
        record.version = organization._version

    @staticmethod
    def to_domain(record: OrganizationRecord) -> Organization:
        return Organization(
            organization_id=OrganizationId(record.id),
            name=record.name,
            status=OrganizationStatus(record.status),
            audit=audit_from_record(
                created_at=record.created_at,
                updated_at=record.updated_at,
            ),
            _version=record.version,
        )
