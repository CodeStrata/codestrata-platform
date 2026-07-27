"""Concrete RepositoryService — Repository Registry use cases."""

from __future__ import annotations

from codestrata_platform.application.commands.repository import (
    ArchiveRepositoryCommand,
    RegisterRepositoryCommand,
    RenameRepositoryCommand,
    UpdateRepositoryMetadataCommand,
)
from codestrata_platform.application.common.errors import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from codestrata_platform.application.common.pagination import PageResult
from codestrata_platform.application.models.repository import (
    RepositoryDetails,
    RepositorySummary,
)
from codestrata_platform.application.queries.repository import RepositoryQuery
from codestrata_platform.domain.organization import OrganizationRepository, OrganizationStatus
from codestrata_platform.domain.repository import (
    Repository,
    RepositoryId,
    RepositoryMetadata,
    RepositoryRepository,
    RepositoryStatus,
)
from codestrata_platform.domain.workspace import WorkspaceRepository, WorkspaceStatus


def normalize_repository_url(url: str) -> str:
    """Normalize SCM URLs for duplicate detection within a workspace."""

    return url.strip().rstrip("/").lower()


class DefaultRepositoryService:
    """Orchestrates Repository aggregate operations via domain ports."""

    def __init__(
        self,
        *,
        repositories: RepositoryRepository,
        workspaces: WorkspaceRepository,
        organizations: OrganizationRepository,
    ) -> None:
        self._repositories = repositories
        self._workspaces = workspaces
        self._organizations = organizations

    def register_repository(self, command: RegisterRepositoryCommand) -> RepositoryDetails:
        organization = self._organizations.get(command.organization_id)
        if organization is None:
            raise NotFoundError(
                f"Organization not found: {command.organization_id.value}",
                reason_code="organization_not_found",
            )
        if organization.status is not OrganizationStatus.ACTIVE:
            raise ValidationError(
                "Cannot register a repository under an inactive organization",
                reason_code="organization_inactive",
            )

        workspace = self._workspaces.get(command.workspace_id)
        if workspace is None:
            raise NotFoundError(
                f"Workspace not found: {command.workspace_id.value}",
                reason_code="workspace_not_found",
            )
        if workspace.status is not WorkspaceStatus.ACTIVE:
            raise ValidationError(
                "Cannot register a repository under an inactive workspace",
                reason_code="workspace_inactive",
            )
        if workspace.organization_id != command.organization_id:
            raise ValidationError(
                "Workspace does not belong to the given organization",
                reason_code="workspace_organization_mismatch",
            )

        normalized_url = normalize_repository_url(command.repository_url)
        for existing in self._repositories.list_by_workspace(command.workspace_id):
            if existing.status is RepositoryStatus.ARCHIVED:
                continue
            if normalize_repository_url(existing.repository_url) == normalized_url:
                raise ConflictError(
                    "A repository with this URL is already registered in the workspace",
                    reason_code="duplicate_repository_url",
                )

        metadata = (
            RepositoryMetadata(dict(command.metadata))
            if command.metadata is not None
            else None
        )
        repository = Repository.register(
            workspace_id=command.workspace_id,
            organization_id=command.organization_id,
            display_name=command.display_name,
            provider=command.provider,
            repository_url=command.repository_url,
            default_branch=command.default_branch,
            visibility=command.visibility,
            description=command.description,
            metadata=metadata,
        )
        self._repositories.save(repository)
        return RepositoryDetails.from_aggregate(repository)

    def get_repository(self, repository_id: RepositoryId) -> RepositoryDetails:
        repository = self._require_repository(repository_id)
        return RepositoryDetails.from_aggregate(repository)

    def list_repositories(self, query: RepositoryQuery) -> PageResult[RepositorySummary]:
        if query.workspace_id is not None:
            candidates = self._repositories.list_by_workspace(query.workspace_id)
        elif query.organization_id is not None:
            candidates = self._repositories.list_by_organization(query.organization_id)
        else:
            # Broad listing is not supported by the domain port; require a scope.
            raise ValidationError(
                "RepositoryQuery requires workspace_id or organization_id",
                reason_code="repository_query_scope_required",
            )

        filtered: list[Repository] = []
        for repository in candidates:
            if query.organization_id is not None and (
                repository.organization_id != query.organization_id
            ):
                continue
            if query.workspace_id is not None and repository.workspace_id != query.workspace_id:
                continue
            if query.status is not None and repository.status is not query.status:
                continue
            if query.provider is not None and repository.provider is not query.provider:
                continue
            filtered.append(repository)

        total = len(filtered)
        page = query.page
        window = filtered[page.offset : page.offset + page.limit]
        items = tuple(RepositoryDetails.from_aggregate(item).to_summary() for item in window)
        return PageResult(items=items, total=total, offset=page.offset, limit=page.limit)

    def archive_repository(self, command: ArchiveRepositoryCommand) -> RepositoryDetails:
        repository = self._require_repository(command.repository_id)
        repository.archive()
        self._repositories.save(repository)
        return RepositoryDetails.from_aggregate(repository)

    def rename_repository(self, command: RenameRepositoryCommand) -> RepositoryDetails:
        repository = self._require_repository(command.repository_id)
        repository.rename(command.display_name)
        self._repositories.save(repository)
        return RepositoryDetails.from_aggregate(repository)

    def update_repository_metadata(
        self,
        command: UpdateRepositoryMetadataCommand,
    ) -> RepositoryDetails:
        repository = self._require_repository(command.repository_id)
        repository.update_metadata(dict(command.updates))
        self._repositories.save(repository)
        return RepositoryDetails.from_aggregate(repository)

    def _require_repository(self, repository_id: RepositoryId) -> Repository:
        repository = self._repositories.get(repository_id)
        if repository is None:
            raise NotFoundError(
                f"Repository not found: {repository_id.value}",
                reason_code="repository_not_found",
            )
        return repository
