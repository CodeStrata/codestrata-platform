"""Organization query models."""

from __future__ import annotations

from dataclasses import dataclass, field

from codestrata_platform.application.common.pagination import PageRequest
from codestrata_platform.domain.organization import OrganizationStatus


@dataclass(frozen=True, slots=True)
class OrganizationQuery:
    status: OrganizationStatus | None = None
    page: PageRequest = field(default_factory=PageRequest)
