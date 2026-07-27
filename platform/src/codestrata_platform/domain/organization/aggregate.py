"""Organization aggregate root.

Organization owns Workspaces. Future billing, users, projects, and portfolio
capabilities attach here without redesigning the aggregate boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from codestrata_platform.domain.errors import (
    InvalidStateTransitionError,
    InvalidValueError,
)
from codestrata_platform.domain.organization.enums import OrganizationStatus
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.shared.audit import AuditInfo


def _require_nonblank(value: str, *, label: str) -> str:
    text = value.strip()
    if not text:
        raise InvalidValueError(
            f"{label} must be non-blank",
            reason_code=f"empty_{label.lower().replace(' ', '_')}",
        )
    return text


@dataclass(slots=True)
class Organization:
    organization_id: OrganizationId
    name: str
    status: OrganizationStatus
    audit: AuditInfo
    _version: int = field(default=0, repr=False)

    def __post_init__(self) -> None:
        self.name = _require_nonblank(self.name, label="Organization name")

    @classmethod
    def create(
        cls,
        *,
        name: str,
        organization_id: OrganizationId | None = None,
        audit: AuditInfo | None = None,
    ) -> Organization:
        return cls(
            organization_id=organization_id or OrganizationId.generate(),
            name=name,
            status=OrganizationStatus.ACTIVE,
            audit=audit or AuditInfo.create(),
        )

    def rename(self, name: str) -> None:
        self._ensure_active()
        self.name = _require_nonblank(name, label="Organization name")
        self._touch()

    def activate(self) -> None:
        if self.status is OrganizationStatus.ACTIVE:
            raise InvalidStateTransitionError(
                "Organization is already active",
                reason_code="organization_already_active",
            )
        self.status = OrganizationStatus.ACTIVE
        self._touch()

    def deactivate(self) -> None:
        if self.status is OrganizationStatus.INACTIVE:
            raise InvalidStateTransitionError(
                "Organization is already inactive",
                reason_code="organization_already_inactive",
            )
        self.status = OrganizationStatus.INACTIVE
        self._touch()

    def _ensure_active(self) -> None:
        if self.status is not OrganizationStatus.ACTIVE:
            raise InvalidStateTransitionError(
                "Inactive organizations cannot be renamed",
                reason_code="organization_inactive",
            )

    def _touch(self) -> None:
        self.audit = self.audit.touch()
        self._version += 1

    def snapshot(self) -> Organization:
        return replace(self, audit=self.audit)
