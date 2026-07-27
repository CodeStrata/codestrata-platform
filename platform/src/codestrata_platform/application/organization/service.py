"""Concrete OrganizationService."""

from __future__ import annotations

from codestrata_platform.application.commands.organization import (
    ActivateOrganizationCommand,
    CreateOrganizationCommand,
    DeactivateOrganizationCommand,
    RenameOrganizationCommand,
)
from codestrata_platform.application.common.errors import NotFoundError
from codestrata_platform.application.common.pagination import PageResult
from codestrata_platform.application.models.organization import OrganizationSummary
from codestrata_platform.application.queries.organization import OrganizationQuery
from codestrata_platform.domain.organization import (
    Organization,
    OrganizationId,
    OrganizationRepository,
)


class DefaultOrganizationService:
    """Orchestrates Organization aggregate operations via domain ports."""

    def __init__(self, *, organizations: OrganizationRepository) -> None:
        self._organizations = organizations

    def create_organization(self, command: CreateOrganizationCommand) -> OrganizationSummary:
        organization = Organization.create(name=command.name)
        self._organizations.save(organization)
        return OrganizationSummary.from_aggregate(organization)

    def get_organization(self, organization_id: OrganizationId) -> OrganizationSummary:
        organization = self._require_organization(organization_id)
        return OrganizationSummary.from_aggregate(organization)

    def list_organizations(self, query: OrganizationQuery) -> PageResult[OrganizationSummary]:
        candidates = self._organizations.list_all()
        filtered = [
            organization
            for organization in candidates
            if query.status is None or organization.status is query.status
        ]
        total = len(filtered)
        page = query.page
        window = filtered[page.offset : page.offset + page.limit]
        items = tuple(OrganizationSummary.from_aggregate(item) for item in window)
        return PageResult(items=items, total=total, offset=page.offset, limit=page.limit)

    def rename_organization(self, command: RenameOrganizationCommand) -> OrganizationSummary:
        organization = self._require_organization(command.organization_id)
        organization.rename(command.name)
        self._organizations.save(organization)
        return OrganizationSummary.from_aggregate(organization)

    def activate_organization(
        self,
        command: ActivateOrganizationCommand,
    ) -> OrganizationSummary:
        organization = self._require_organization(command.organization_id)
        organization.activate()
        self._organizations.save(organization)
        return OrganizationSummary.from_aggregate(organization)

    def deactivate_organization(
        self,
        command: DeactivateOrganizationCommand,
    ) -> OrganizationSummary:
        organization = self._require_organization(command.organization_id)
        organization.deactivate()
        self._organizations.save(organization)
        return OrganizationSummary.from_aggregate(organization)

    def _require_organization(self, organization_id: OrganizationId) -> Organization:
        organization = self._organizations.get(organization_id)
        if organization is None:
            raise NotFoundError(
                f"Organization not found: {organization_id.value}",
                reason_code="organization_not_found",
            )
        return organization
