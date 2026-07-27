"""Organization application models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from codestrata_platform.domain.organization import (
    Organization,
    OrganizationId,
    OrganizationStatus,
)


@dataclass(frozen=True, slots=True)
class OrganizationSummary:
    organization_id: OrganizationId
    name: str
    status: OrganizationStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_aggregate(cls, organization: Organization) -> OrganizationSummary:
        return cls(
            organization_id=organization.organization_id,
            name=organization.name,
            status=organization.status,
            created_at=organization.audit.created_at.value,
            updated_at=organization.audit.updated_at.value,
        )
