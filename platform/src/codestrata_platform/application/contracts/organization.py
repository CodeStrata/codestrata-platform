"""OrganizationService contract."""

from __future__ import annotations

from typing import Protocol

from codestrata_platform.application.commands.organization import (
    ActivateOrganizationCommand,
    CreateOrganizationCommand,
    DeactivateOrganizationCommand,
    RenameOrganizationCommand,
)
from codestrata_platform.application.common.pagination import PageResult
from codestrata_platform.application.models.organization import OrganizationSummary
from codestrata_platform.application.queries.organization import OrganizationQuery
from codestrata_platform.domain.organization import OrganizationId


class OrganizationService(Protocol):
    """Application contract for organization lifecycle operations."""

    def create_organization(self, command: CreateOrganizationCommand) -> OrganizationSummary:
        """Create an active organization."""

    def get_organization(self, organization_id: OrganizationId) -> OrganizationSummary:
        """Return an organization or raise when missing."""

    def list_organizations(self, query: OrganizationQuery) -> PageResult[OrganizationSummary]:
        """List organizations matching the query."""

    def rename_organization(self, command: RenameOrganizationCommand) -> OrganizationSummary:
        """Rename an organization."""

    def activate_organization(
        self,
        command: ActivateOrganizationCommand,
    ) -> OrganizationSummary:
        """Activate an organization."""

    def deactivate_organization(
        self,
        command: DeactivateOrganizationCommand,
    ) -> OrganizationSummary:
        """Deactivate an organization."""
