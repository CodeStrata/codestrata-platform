"""EngineeringPortfolio aggregate root."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime

from codestrata_platform.domain.errors import (
    InvalidStateTransitionError,
    InvariantViolationError,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.errors import PortfolioMembershipError
from codestrata_platform.domain.portfolio.identifiers import (
    PortfolioDescription,
    PortfolioId,
    PortfolioMembershipId,
    PortfolioName,
)
from codestrata_platform.domain.portfolio.lifecycle import (
    PortfolioStatus,
    RepositoryCriticality,
)
from codestrata_platform.domain.portfolio.membership import (
    PortfolioMembership,
    PortfolioRepositoryReference,
)
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.shared.audit import AuditInfo
from codestrata_platform.domain.workspace.ids import WorkspaceId

DEFAULT_MAX_REPOSITORIES = 500
HARD_MAX_REPOSITORIES = 2000


@dataclass(slots=True)
class EngineeringPortfolio:
    """Commercial portfolio of same-tenant repositories."""

    portfolio_id: PortfolioId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    name: PortfolioName
    description: PortfolioDescription
    status: PortfolioStatus
    memberships: tuple[PortfolioMembership, ...]
    audit: AuditInfo
    archived_at: datetime | None = None
    max_repositories: int = DEFAULT_MAX_REPOSITORIES
    _version: int = field(default=0, repr=False)

    def __post_init__(self) -> None:
        if self.max_repositories < 1 or self.max_repositories > HARD_MAX_REPOSITORIES:
            raise InvariantViolationError(
                f"max_repositories must be between 1 and {HARD_MAX_REPOSITORIES}",
                reason_code="invalid_portfolio_repository_limit",
            )

    @classmethod
    def create(
        cls,
        *,
        organization_id: OrganizationId,
        workspace_id: WorkspaceId,
        name: str,
        description: str | None = None,
        portfolio_id: PortfolioId | None = None,
        max_repositories: int = DEFAULT_MAX_REPOSITORIES,
        audit: AuditInfo | None = None,
    ) -> EngineeringPortfolio:
        return cls(
            portfolio_id=portfolio_id or PortfolioId.generate(),
            organization_id=organization_id,
            workspace_id=workspace_id,
            name=PortfolioName(name),
            description=PortfolioDescription(description),
            status=PortfolioStatus.ACTIVE,
            memberships=(),
            audit=audit or AuditInfo.create(),
            max_repositories=max_repositories,
        )

    @property
    def active_memberships(self) -> tuple[PortfolioMembership, ...]:
        return tuple(item for item in self.memberships if item.is_active)

    def rename(self, name: str) -> None:
        self._ensure_active()
        self.name = PortfolioName(name)
        self._touch()

    def update_description(self, description: str | None) -> None:
        self._ensure_active()
        self.description = PortfolioDescription(description)
        self._touch()

    def add_repository(
        self,
        reference: PortfolioRepositoryReference,
        *,
        criticality: RepositoryCriticality = RepositoryCriticality.UNSPECIFIED,
        business_capability: str | None = None,
        owner_reference: str | None = None,
        lifecycle_status: str | None = None,
        tags: tuple[str, ...] = (),
        membership_id: PortfolioMembershipId | None = None,
    ) -> PortfolioMembership:
        self._ensure_active()
        if (
            reference.organization_id != self.organization_id
            or reference.workspace_id != self.workspace_id
        ):
            raise PortfolioMembershipError(
                "Repository membership must belong to the same organization and workspace",
                reason_code="cross_tenant_membership",
            )
        if any(
            item.repository_id == reference.repository_id and item.is_active
            for item in self.memberships
        ):
            raise PortfolioMembershipError(
                "Repository is already an active portfolio member",
                reason_code="duplicate_membership",
            )
        if len(self.active_memberships) >= self.max_repositories:
            raise PortfolioMembershipError(
                f"Portfolio may contain at most {self.max_repositories} repositories",
                reason_code="portfolio_repository_limit",
            )
        membership = PortfolioMembership(
            membership_id=membership_id or PortfolioMembershipId.generate(),
            portfolio_id=self.portfolio_id,
            organization_id=self.organization_id,
            workspace_id=self.workspace_id,
            repository_id=reference.repository_id,
            criticality=criticality,
            business_capability=business_capability,
            owner_reference=owner_reference,
            lifecycle_status=lifecycle_status,
            tags=tags,
        )
        self.memberships = (*self.memberships, membership)
        self._touch()
        return membership

    def remove_repository(self, repository_id: RepositoryId) -> PortfolioMembership | None:
        self._ensure_active()
        updated: list[PortfolioMembership] = []
        removed: PortfolioMembership | None = None
        for item in self.memberships:
            if item.repository_id == repository_id and item.is_active:
                copy = item.snapshot()
                copy.remove()
                removed = copy
                updated.append(copy)
            else:
                updated.append(item)
        if removed is None:
            return None
        self.memberships = tuple(updated)
        self._touch()
        return removed

    def activate(self) -> None:
        if self.status is PortfolioStatus.ACTIVE:
            raise InvalidStateTransitionError(
                "Portfolio is already active",
                reason_code="portfolio_already_active",
            )
        self.status = PortfolioStatus.ACTIVE
        self.archived_at = None
        self._touch()

    def archive(self) -> None:
        if self.status is PortfolioStatus.ARCHIVED:
            raise InvalidStateTransitionError(
                "Portfolio is already archived",
                reason_code="portfolio_already_archived",
            )
        self.status = PortfolioStatus.ARCHIVED
        self.archived_at = datetime.now(UTC)
        self._touch()

    def _ensure_active(self) -> None:
        if self.status is not PortfolioStatus.ACTIVE:
            raise InvalidStateTransitionError(
                "Archived portfolios cannot be modified",
                reason_code="portfolio_archived",
            )

    def _touch(self) -> None:
        self.audit = self.audit.touch()
        self._version += 1

    def snapshot(self) -> EngineeringPortfolio:
        return replace(
            self,
            memberships=tuple(item.snapshot() for item in self.memberships),
            audit=self.audit,
        )
