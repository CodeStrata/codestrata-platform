"""Repository aggregate ↔ RepositoryRecord mapper."""

from __future__ import annotations

from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository import (
    Repository,
    RepositoryId,
    RepositoryMetadata,
    RepositoryProvider,
    RepositoryStatus,
    RepositoryVisibility,
)
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.infrastructure.persistence.mappers._helpers import (
    audit_from_record,
    normalize_repository_url,
)
from codestrata_platform.infrastructure.persistence.models.repository_record import (
    RepositoryRecord,
)


class RepositoryMapper:
    @staticmethod
    def to_record(repository: Repository) -> RepositoryRecord:
        return RepositoryRecord(
            id=repository.repository_id.value,
            workspace_id=repository.workspace_id.value,
            organization_id=repository.organization_id.value,
            display_name=repository.display_name,
            provider=repository.provider.value,
            repository_url=repository.repository_url,
            normalized_url=normalize_repository_url(repository.repository_url),
            default_branch=repository.default_branch,
            visibility=repository.visibility.value,
            description=repository.description,
            status=repository.status.value,
            metadata_json=dict(repository.metadata.attributes),
            created_at=repository.audit.created_at.value,
            updated_at=repository.audit.updated_at.value,
            version=repository._version,
        )

    @staticmethod
    def apply_to_record(repository: Repository, record: RepositoryRecord) -> None:
        record.workspace_id = repository.workspace_id.value
        record.organization_id = repository.organization_id.value
        record.display_name = repository.display_name
        record.provider = repository.provider.value
        record.repository_url = repository.repository_url
        record.normalized_url = normalize_repository_url(repository.repository_url)
        record.default_branch = repository.default_branch
        record.visibility = repository.visibility.value
        record.description = repository.description
        record.status = repository.status.value
        record.metadata_json = dict(repository.metadata.attributes)
        record.created_at = repository.audit.created_at.value
        record.updated_at = repository.audit.updated_at.value
        record.version = repository._version

    @staticmethod
    def to_domain(record: RepositoryRecord) -> Repository:
        return Repository(
            repository_id=RepositoryId(record.id),
            workspace_id=WorkspaceId(record.workspace_id),
            organization_id=OrganizationId(record.organization_id),
            display_name=record.display_name,
            provider=RepositoryProvider(record.provider),
            repository_url=record.repository_url,
            default_branch=record.default_branch,
            visibility=RepositoryVisibility(record.visibility),
            description=record.description,
            status=RepositoryStatus(record.status),
            metadata=RepositoryMetadata(dict(record.metadata_json or {})),
            audit=audit_from_record(
                created_at=record.created_at,
                updated_at=record.updated_at,
            ),
            _version=record.version,
        )
