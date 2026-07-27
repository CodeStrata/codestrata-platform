"""Portfolio repository membership value objects."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioMembershipId
from codestrata_platform.domain.portfolio.lifecycle import RepositoryCriticality
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId

_MAX_TAGS = 32
_MAX_TAG_LEN = 64
_MAX_LABEL = 256


def _optional_bounded(
    value: str | None,
    *,
    field_name: str,
    max_length: int = _MAX_LABEL,
) -> str | None:
    if value is None:
        return None
    compact = value.strip()
    if not compact:
        return None
    if len(compact) > max_length:
        raise InvalidValueError(
            f"{field_name} exceeds maximum length of {max_length}",
            reason_code=f"{field_name}_too_long",
        )
    return compact


@dataclass(frozen=True, slots=True)
class PortfolioRepositoryReference:
    """Bounded reference to a repository eligible for portfolio membership."""

    organization_id: OrganizationId
    workspace_id: WorkspaceId
    repository_id: RepositoryId


@dataclass(slots=True)
class PortfolioMembership:
    membership_id: PortfolioMembershipId
    portfolio_id: PortfolioId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    repository_id: RepositoryId
    criticality: RepositoryCriticality = RepositoryCriticality.UNSPECIFIED
    business_capability: str | None = None
    owner_reference: str | None = None
    lifecycle_status: str | None = None
    tags: tuple[str, ...] = ()
    added_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    removed_at: datetime | None = None

    def __post_init__(self) -> None:
        self.business_capability = _optional_bounded(
            self.business_capability,
            field_name="business_capability",
        )
        self.owner_reference = _optional_bounded(
            self.owner_reference,
            field_name="owner_reference",
        )
        self.lifecycle_status = _optional_bounded(
            self.lifecycle_status,
            field_name="lifecycle_status",
            max_length=64,
        )
        cleaned: list[str] = []
        for tag in self.tags:
            compact = tag.strip()
            if not compact:
                continue
            if len(compact) > _MAX_TAG_LEN:
                raise InvalidValueError(
                    "Membership tag exceeds maximum length",
                    reason_code="membership_tag_too_long",
                )
            cleaned.append(compact)
        if len(cleaned) > _MAX_TAGS:
            raise InvalidValueError(
                f"Membership may contain at most {_MAX_TAGS} tags",
                reason_code="membership_tags_too_large",
            )
        self.tags = tuple(sorted(set(cleaned)))

    @property
    def is_active(self) -> bool:
        return self.removed_at is None

    def update_metadata(
        self,
        *,
        criticality: RepositoryCriticality | None = None,
        business_capability: str | None = None,
        owner_reference: str | None = None,
        lifecycle_status: str | None = None,
        tags: tuple[str, ...] | None = None,
    ) -> None:
        if criticality is not None:
            self.criticality = criticality
        if business_capability is not None:
            self.business_capability = _optional_bounded(
                business_capability,
                field_name="business_capability",
            )
        if owner_reference is not None:
            self.owner_reference = _optional_bounded(
                owner_reference,
                field_name="owner_reference",
            )
        if lifecycle_status is not None:
            self.lifecycle_status = _optional_bounded(
                lifecycle_status,
                field_name="lifecycle_status",
                max_length=64,
            )
        if tags is not None:
            cleaned: list[str] = []
            for tag in tags:
                compact = tag.strip()
                if not compact:
                    continue
                if len(compact) > _MAX_TAG_LEN:
                    raise InvalidValueError(
                        "Membership tag exceeds maximum length",
                        reason_code="membership_tag_too_long",
                    )
                cleaned.append(compact)
            if len(cleaned) > _MAX_TAGS:
                raise InvalidValueError(
                    f"Membership may contain at most {_MAX_TAGS} tags",
                    reason_code="membership_tags_too_large",
                )
            self.tags = tuple(sorted(set(cleaned)))

    def remove(self, *, at: datetime | None = None) -> None:
        if self.removed_at is not None:
            return
        self.removed_at = at or datetime.now(UTC)

    def snapshot(self) -> PortfolioMembership:
        return replace(self)
