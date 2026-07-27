"""Organization aggregate for multi-tenant Platform tenancy."""

from __future__ import annotations

from codestrata_platform.domain.organization.aggregate import Organization
from codestrata_platform.domain.organization.enums import OrganizationStatus
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.organization.ports import OrganizationRepository

__all__ = [
    "Organization",
    "OrganizationId",
    "OrganizationRepository",
    "OrganizationStatus",
]
