"""Workspace aggregate root."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from codestrata_platform.domain.errors import (
    InvalidStateTransitionError,
    InvalidValueError,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.shared.audit import AuditInfo
from codestrata_platform.domain.workspace.enums import WorkspaceStatus
from codestrata_platform.domain.workspace.ids import WorkspaceId


def _require_nonblank(value: str, *, label: str) -> str:
    text = value.strip()
    if not text:
        raise InvalidValueError(
            f"{label} must be non-blank",
            reason_code=f"empty_{label.lower().replace(' ', '_')}",
        )
    return text


@dataclass(slots=True)
class Workspace:
    """Isolated customer environment owned by an Organization."""

    workspace_id: WorkspaceId
    organization_id: OrganizationId
    name: str
    description: str | None
    status: WorkspaceStatus
    audit: AuditInfo
    _version: int = field(default=0, repr=False)

    def __post_init__(self) -> None:
        self.name = _require_nonblank(self.name, label="Workspace name")
        if self.description is not None:
            compact = self.description.strip()
            self.description = compact or None

    @classmethod
    def create(
        cls,
        *,
        organization_id: OrganizationId,
        name: str,
        description: str | None = None,
        workspace_id: WorkspaceId | None = None,
        audit: AuditInfo | None = None,
    ) -> Workspace:
        return cls(
            workspace_id=workspace_id or WorkspaceId.generate(),
            organization_id=organization_id,
            name=name,
            description=description,
            status=WorkspaceStatus.ACTIVE,
            audit=audit or AuditInfo.create(),
        )

    def rename(self, name: str) -> None:
        self._ensure_active()
        self.name = _require_nonblank(name, label="Workspace name")
        self._touch()

    def activate(self) -> None:
        if self.status is WorkspaceStatus.ACTIVE:
            raise InvalidStateTransitionError(
                "Workspace is already active",
                reason_code="workspace_already_active",
            )
        self.status = WorkspaceStatus.ACTIVE
        self._touch()

    def deactivate(self) -> None:
        if self.status is WorkspaceStatus.INACTIVE:
            raise InvalidStateTransitionError(
                "Workspace is already inactive",
                reason_code="workspace_already_inactive",
            )
        self.status = WorkspaceStatus.INACTIVE
        self._touch()

    def _ensure_active(self) -> None:
        if self.status is not WorkspaceStatus.ACTIVE:
            raise InvalidStateTransitionError(
                "Inactive workspaces cannot be renamed",
                reason_code="workspace_inactive",
            )

    def _touch(self) -> None:
        self.audit = self.audit.touch()
        self._version += 1

    def snapshot(self) -> Workspace:
        return replace(self, audit=self.audit)
