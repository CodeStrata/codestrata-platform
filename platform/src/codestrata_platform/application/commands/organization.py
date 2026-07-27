"""Organization lifecycle commands."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.organization.ids import OrganizationId


@dataclass(frozen=True, slots=True)
class CreateOrganizationCommand:
    name: str


@dataclass(frozen=True, slots=True)
class RenameOrganizationCommand:
    organization_id: OrganizationId
    name: str


@dataclass(frozen=True, slots=True)
class ActivateOrganizationCommand:
    organization_id: OrganizationId


@dataclass(frozen=True, slots=True)
class DeactivateOrganizationCommand:
    organization_id: OrganizationId
