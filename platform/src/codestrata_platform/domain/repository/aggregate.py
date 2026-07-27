"""Repository aggregate root."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from codestrata_platform.domain.errors import (
    InvalidStateTransitionError,
    InvalidValueError,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.enums import (
    RepositoryProvider,
    RepositoryStatus,
    RepositoryVisibility,
)
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.repository.value_objects import RepositoryMetadata
from codestrata_platform.domain.shared.audit import AuditInfo
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
class Repository:
    """Registered SCM repository known to the Commercial Platform.

    No cloning or synchronization behavior lives here—registration only.
    """

    repository_id: RepositoryId
    workspace_id: WorkspaceId
    organization_id: OrganizationId
    display_name: str
    provider: RepositoryProvider
    repository_url: str
    default_branch: str
    visibility: RepositoryVisibility
    description: str | None
    status: RepositoryStatus
    metadata: RepositoryMetadata
    audit: AuditInfo
    _version: int = field(default=0, repr=False)

    def __post_init__(self) -> None:
        self.display_name = _require_nonblank(self.display_name, label="Display name")
        self.repository_url = _require_nonblank(self.repository_url, label="Repository URL")
        self.default_branch = _require_nonblank(self.default_branch, label="Default branch")
        if self.description is not None:
            compact = self.description.strip()
            self.description = compact or None

    @classmethod
    def register(
        cls,
        *,
        workspace_id: WorkspaceId,
        organization_id: OrganizationId,
        display_name: str,
        provider: RepositoryProvider,
        repository_url: str,
        default_branch: str = "main",
        visibility: RepositoryVisibility = RepositoryVisibility.PRIVATE,
        description: str | None = None,
        metadata: RepositoryMetadata | None = None,
        repository_id: RepositoryId | None = None,
        audit: AuditInfo | None = None,
    ) -> Repository:
        return cls(
            repository_id=repository_id or RepositoryId.generate(),
            workspace_id=workspace_id,
            organization_id=organization_id,
            display_name=display_name,
            provider=provider,
            repository_url=repository_url,
            default_branch=default_branch,
            visibility=visibility,
            description=description,
            status=RepositoryStatus.ACTIVE,
            metadata=metadata or RepositoryMetadata.empty(),
            audit=audit or AuditInfo.create(),
        )

    @property
    def is_archived(self) -> bool:
        return self.status is RepositoryStatus.ARCHIVED

    def rename(self, display_name: str) -> None:
        self._ensure_active()
        self.display_name = _require_nonblank(display_name, label="Display name")
        self._touch()

    def update_metadata(self, updates: dict[str, str]) -> None:
        self._ensure_active()
        self.metadata = self.metadata.merge(updates)
        self._touch()

    def archive(self) -> None:
        if self.status is RepositoryStatus.ARCHIVED:
            raise InvalidStateTransitionError(
                "Repository is already archived",
                reason_code="repository_already_archived",
            )
        self.status = RepositoryStatus.ARCHIVED
        self._touch()

    def _ensure_active(self) -> None:
        if self.status is not RepositoryStatus.ACTIVE:
            raise InvalidStateTransitionError(
                "Archived repositories cannot be modified",
                reason_code="repository_archived",
            )

    def _touch(self) -> None:
        self.audit = self.audit.touch()
        self._version += 1

    def snapshot(self) -> Repository:
        """Return a detached copy for read models / optimistic concurrency."""

        return replace(self, metadata=self.metadata, audit=self.audit)
