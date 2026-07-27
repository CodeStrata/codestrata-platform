"""PortfolioRetrievalIndex aggregate."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime

from codestrata_platform.domain.errors import InvalidStateTransitionError, InvalidValueError
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.portfolio_retrieval.chunk import PortfolioRetrievalChunk
from codestrata_platform.domain.portfolio_retrieval.document import PortfolioRetrievalDocument
from codestrata_platform.domain.portfolio_retrieval.errors import PortfolioRetrievalInvariantError
from codestrata_platform.domain.portfolio_retrieval.identifiers import (
    EmbeddingDimension,
    EmbeddingModelId,
    EmbeddingProviderId,
    PortfolioRetrievalIndexId,
    PortfolioRetrievalProjectionKey,
)
from codestrata_platform.domain.portfolio_retrieval.lifecycle import (
    PortfolioRetrievalIndexStatus,
    PortfolioRetrievalIndexVersion,
)
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.shared.audit import AuditInfo
from codestrata_platform.domain.workspace.ids import WorkspaceId

HARD_MAX_INDEX_REPOSITORIES = 2000


@dataclass(slots=True)
class PortfolioRetrievalIndex:
    """Rebuildable portfolio-scoped projection of Platform intelligence for retrieval."""

    index_id: PortfolioRetrievalIndexId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    portfolio_id: PortfolioId
    portfolio_snapshot_id: PortfolioSnapshotId
    portfolio_snapshot_version: int
    index_version: PortfolioRetrievalIndexVersion
    status: PortfolioRetrievalIndexStatus
    projection_key: PortfolioRetrievalProjectionKey
    retrieval_schema_version: str
    chunking_policy_version: str
    ranking_policy_version: str
    embedding_provider_id: EmbeddingProviderId
    embedding_model_id: EmbeddingModelId
    embedding_dimension: EmbeddingDimension
    repository_ids: tuple[RepositoryId, ...]
    documents: tuple[PortfolioRetrievalDocument, ...]
    chunks: tuple[PortfolioRetrievalChunk, ...]
    audit: AuditInfo
    completed_at: datetime | None = None
    superseded_at: datetime | None = None
    failure_reason: str | None = None
    _version: int = field(default=0, repr=False)

    def __post_init__(self) -> None:
        self.retrieval_schema_version = self.retrieval_schema_version.strip()
        self.chunking_policy_version = self.chunking_policy_version.strip()
        self.ranking_policy_version = self.ranking_policy_version.strip()
        if (
            not self.retrieval_schema_version
            or not self.chunking_policy_version
            or not self.ranking_policy_version
        ):
            raise InvalidValueError(
                "schema/chunking/ranking policy versions must be non-blank",
                reason_code="empty_portfolio_retrieval_version",
            )
        if len(self.repository_ids) > HARD_MAX_INDEX_REPOSITORIES:
            raise InvalidValueError(
                "repository_ids exceeds maximum of "
                f"{HARD_MAX_INDEX_REPOSITORIES} repositories",
                reason_code="portfolio_retrieval_index_repositories_too_large",
            )
        self._assert_integrity()

    @classmethod
    def create_pending(
        cls,
        *,
        index_id: PortfolioRetrievalIndexId,
        organization_id: OrganizationId,
        workspace_id: WorkspaceId,
        portfolio_id: PortfolioId,
        portfolio_snapshot_id: PortfolioSnapshotId,
        portfolio_snapshot_version: int,
        index_version: int,
        projection_key: PortfolioRetrievalProjectionKey,
        retrieval_schema_version: str,
        chunking_policy_version: str,
        ranking_policy_version: str,
        embedding_provider_id: EmbeddingProviderId,
        embedding_model_id: EmbeddingModelId,
        embedding_dimension: EmbeddingDimension,
        repository_ids: tuple[RepositoryId, ...] = (),
    ) -> PortfolioRetrievalIndex:
        return cls(
            index_id=index_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            portfolio_id=portfolio_id,
            portfolio_snapshot_id=portfolio_snapshot_id,
            portfolio_snapshot_version=portfolio_snapshot_version,
            index_version=PortfolioRetrievalIndexVersion(index_version),
            status=PortfolioRetrievalIndexStatus.PENDING,
            projection_key=projection_key,
            retrieval_schema_version=retrieval_schema_version,
            chunking_policy_version=chunking_policy_version,
            ranking_policy_version=ranking_policy_version,
            embedding_provider_id=embedding_provider_id,
            embedding_model_id=embedding_model_id,
            embedding_dimension=embedding_dimension,
            repository_ids=repository_ids,
            documents=(),
            chunks=(),
            audit=AuditInfo.create(),
        )

    def begin_indexing(self) -> None:
        self._require_mutable()
        if self.status is not PortfolioRetrievalIndexStatus.PENDING:
            raise InvalidStateTransitionError(
                f"Cannot begin indexing from status {self.status.value}",
                reason_code="invalid_begin_portfolio_retrieval_indexing",
            )
        self.status = PortfolioRetrievalIndexStatus.INDEXING
        self._touch()

    def add_document(self, document: PortfolioRetrievalDocument) -> None:
        self._require_indexing()
        if document.index_id != self.index_id:
            raise PortfolioRetrievalInvariantError(
                "Document index_id mismatch",
                reason_code="portfolio_retrieval_document_index_mismatch",
            )
        if document.portfolio_id != self.portfolio_id:
            raise PortfolioRetrievalInvariantError(
                "Document portfolio_id mismatch",
                reason_code="portfolio_retrieval_document_portfolio_mismatch",
            )
        if document.portfolio_snapshot_id != self.portfolio_snapshot_id:
            raise PortfolioRetrievalInvariantError(
                "Document portfolio_snapshot_id mismatch",
                reason_code="portfolio_retrieval_document_snapshot_mismatch",
            )
        existing = {item.document_id.value: item for item in self.documents}
        prior = existing.get(document.document_id.value)
        if prior is not None:
            if prior.checksum != document.checksum:
                raise PortfolioRetrievalInvariantError(
                    "Conflicting document checksum",
                    reason_code="portfolio_retrieval_duplicate_document_conflict",
                )
            return
        self.documents = (*self.documents, document)
        self._touch()

    def add_chunk(self, chunk: PortfolioRetrievalChunk) -> None:
        self._require_indexing()
        if chunk.index_id != self.index_id:
            raise PortfolioRetrievalInvariantError(
                "Chunk index_id mismatch",
                reason_code="portfolio_retrieval_chunk_index_mismatch",
            )
        if chunk.portfolio_id != self.portfolio_id:
            raise PortfolioRetrievalInvariantError(
                "Chunk portfolio_id mismatch",
                reason_code="portfolio_retrieval_chunk_portfolio_mismatch",
            )
        if chunk.portfolio_snapshot_id != self.portfolio_snapshot_id:
            raise PortfolioRetrievalInvariantError(
                "Chunk portfolio_snapshot_id mismatch",
                reason_code="portfolio_retrieval_chunk_snapshot_mismatch",
            )
        document_ids = {item.document_id.value for item in self.documents}
        if chunk.document_id.value not in document_ids:
            raise PortfolioRetrievalInvariantError(
                "Chunk references unknown document",
                reason_code="portfolio_retrieval_chunk_document_missing",
            )
        if chunk.embedding is not None:
            if chunk.embedding.dimension != self.embedding_dimension.value:
                raise PortfolioRetrievalInvariantError(
                    "Embedding dimension mismatch",
                    reason_code="portfolio_retrieval_embedding_dimension_mismatch",
                )
        for existing in self.chunks:
            if existing.chunk_id.value == chunk.chunk_id.value:
                if existing.checksum.value != chunk.checksum.value:
                    raise PortfolioRetrievalInvariantError(
                        "Conflicting chunk checksum",
                        reason_code="portfolio_retrieval_duplicate_chunk_conflict",
                    )
                return
            if (
                existing.document_id == chunk.document_id
                and existing.checksum.value == chunk.checksum.value
            ):
                return
        self.chunks = (*self.chunks, chunk)
        self._touch()

    def complete(self) -> None:
        self._require_indexing()
        self._assert_integrity()
        if not self.documents or not self.chunks:
            raise PortfolioRetrievalInvariantError(
                "Completed index requires documents and chunks",
                reason_code="empty_portfolio_retrieval_index",
            )
        for chunk in self.chunks:
            if chunk.embedding is None:
                raise PortfolioRetrievalInvariantError(
                    "All chunks must be embedded before completion",
                    reason_code="missing_portfolio_retrieval_chunk_embedding",
                )
        self.status = PortfolioRetrievalIndexStatus.COMPLETED
        self.completed_at = datetime.now(UTC)
        self.failure_reason = None
        self._touch()

    def fail(self, reason: str) -> None:
        self._require_mutable()
        if self.status not in {
            PortfolioRetrievalIndexStatus.PENDING,
            PortfolioRetrievalIndexStatus.INDEXING,
        }:
            raise InvalidStateTransitionError(
                f"Cannot fail index in status {self.status.value}",
                reason_code="invalid_portfolio_retrieval_fail_transition",
            )
        compact = reason.strip()
        if not compact:
            raise InvalidValueError(
                "failure reason must be non-blank",
                reason_code="empty_portfolio_retrieval_failure_reason",
            )
        self.status = PortfolioRetrievalIndexStatus.FAILED
        self.failure_reason = compact[:1000]
        self.documents = ()
        self.chunks = ()
        self._touch()

    def supersede(self) -> None:
        if self.status is not PortfolioRetrievalIndexStatus.COMPLETED:
            raise InvalidStateTransitionError(
                f"Cannot supersede index in status {self.status.value}",
                reason_code="invalid_portfolio_retrieval_supersede_transition",
            )
        self.status = PortfolioRetrievalIndexStatus.SUPERSEDED
        self.superseded_at = datetime.now(UTC)
        self._touch()

    def archive(self) -> None:
        if self.status not in {
            PortfolioRetrievalIndexStatus.COMPLETED,
            PortfolioRetrievalIndexStatus.SUPERSEDED,
        }:
            raise InvalidStateTransitionError(
                f"Cannot archive index in status {self.status.value}",
                reason_code="invalid_portfolio_retrieval_archive_transition",
            )
        self.status = PortfolioRetrievalIndexStatus.ARCHIVED
        self._touch()

    def snapshot(self) -> PortfolioRetrievalIndex:
        return replace(self)

    def _touch(self) -> None:
        self.audit = self.audit.touch()
        self._version += 1

    def _require_mutable(self) -> None:
        if self.status is PortfolioRetrievalIndexStatus.COMPLETED:
            raise InvalidStateTransitionError(
                "Completed portfolio retrieval indexes are immutable",
                reason_code="portfolio_retrieval_index_immutable",
            )
        if self.status in {
            PortfolioRetrievalIndexStatus.SUPERSEDED,
            PortfolioRetrievalIndexStatus.ARCHIVED,
            PortfolioRetrievalIndexStatus.FAILED,
        }:
            raise InvalidStateTransitionError(
                f"Index in status {self.status.value} is immutable",
                reason_code="portfolio_retrieval_index_immutable",
            )

    def _require_indexing(self) -> None:
        self._require_mutable()
        if self.status is not PortfolioRetrievalIndexStatus.INDEXING:
            raise InvalidStateTransitionError(
                f"Cannot mutate index contents in status {self.status.value}",
                reason_code="portfolio_retrieval_index_not_indexing",
            )

    def _assert_integrity(self) -> None:
        document_ids = [item.document_id.value for item in self.documents]
        if len(document_ids) != len(set(document_ids)):
            raise PortfolioRetrievalInvariantError(
                "Document ids must be unique within an index",
                reason_code="portfolio_retrieval_duplicate_document_id",
            )
        chunk_ids = [item.chunk_id.value for item in self.chunks]
        if len(chunk_ids) != len(set(chunk_ids)):
            raise PortfolioRetrievalInvariantError(
                "Chunk ids must be unique within an index",
                reason_code="portfolio_retrieval_duplicate_chunk_id",
            )
        known = set(document_ids)
        for document in self.documents:
            if document.portfolio_id != self.portfolio_id:
                raise PortfolioRetrievalInvariantError(
                    "Documents must belong to the index portfolio",
                    reason_code="portfolio_retrieval_document_portfolio_mismatch",
                )
            if document.portfolio_snapshot_id != self.portfolio_snapshot_id:
                raise PortfolioRetrievalInvariantError(
                    "Documents must belong to the index portfolio snapshot",
                    reason_code="portfolio_retrieval_document_snapshot_mismatch",
                )
        for chunk in self.chunks:
            if chunk.document_id.value not in known:
                raise PortfolioRetrievalInvariantError(
                    "Chunks may only reference documents in the same index",
                    reason_code="portfolio_retrieval_chunk_document_mismatch",
                )
            if chunk.portfolio_id != self.portfolio_id:
                raise PortfolioRetrievalInvariantError(
                    "Chunks must belong to the index portfolio",
                    reason_code="portfolio_retrieval_chunk_portfolio_mismatch",
                )
            if chunk.portfolio_snapshot_id != self.portfolio_snapshot_id:
                raise PortfolioRetrievalInvariantError(
                    "Chunks must belong to the index portfolio snapshot",
                    reason_code="portfolio_retrieval_chunk_snapshot_mismatch",
                )
