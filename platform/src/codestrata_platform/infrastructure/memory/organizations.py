"""In-memory OrganizationRepository."""

from __future__ import annotations

from codestrata_platform.domain.organization import Organization, OrganizationId


class InMemoryOrganizationRepository:
    """Temporary store for Organization aggregates."""

    def __init__(self) -> None:
        self._items: dict[str, Organization] = {}

    def get(self, organization_id: OrganizationId) -> Organization | None:
        item = self._items.get(organization_id.value)
        return item.snapshot() if item is not None else None

    def save(self, organization: Organization) -> None:
        self._items[organization.organization_id.value] = organization.snapshot()

    def list_all(self) -> tuple[Organization, ...]:
        return tuple(item.snapshot() for item in self._items.values())
