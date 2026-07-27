"""Portfolio retrieval scope value objects."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId

HARD_MAX_SCOPE_REPOSITORIES = 2000


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalScope:
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    portfolio_id: PortfolioId
    portfolio_snapshot_id: PortfolioSnapshotId | None = None
    repository_ids: tuple[RepositoryId, ...] = ()
    exclude_repository_ids: tuple[RepositoryId, ...] = ()

    def __post_init__(self) -> None:
        if len(self.repository_ids) > HARD_MAX_SCOPE_REPOSITORIES:
            raise InvalidValueError(
                f"repository_ids may contain at most {HARD_MAX_SCOPE_REPOSITORIES} entries",
                reason_code="portfolio_retrieval_scope_repositories_too_large",
            )
        if len(self.exclude_repository_ids) > HARD_MAX_SCOPE_REPOSITORIES:
            raise InvalidValueError(
                "exclude_repository_ids may contain at most "
                f"{HARD_MAX_SCOPE_REPOSITORIES} entries",
                reason_code="portfolio_retrieval_scope_exclusions_too_large",
            )
        included = set(self.repository_ids)
        excluded = set(self.exclude_repository_ids)
        if included & excluded:
            raise InvalidValueError(
                "repository_ids and exclude_repository_ids must not overlap",
                reason_code="portfolio_retrieval_scope_conflicting_repositories",
            )
