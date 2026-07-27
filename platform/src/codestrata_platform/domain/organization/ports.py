"""Persistence port for the Organization aggregate."""

from __future__ import annotations

from typing import Protocol

from codestrata_platform.domain.organization.aggregate import Organization
from codestrata_platform.domain.organization.ids import OrganizationId


class OrganizationRepository(Protocol):
    """Organization port — no persistence implementation in Phase 8.1.1."""

    def get(self, organization_id: OrganizationId) -> Organization | None:
        """Load an organization by id, or None when absent."""

    def save(self, organization: Organization) -> None:
        """Insert or update an organization aggregate."""

    def list_all(self) -> tuple[Organization, ...]:
        """List organizations (tenant registry)."""
