"""EngineeringRetrievalIndex aggregate."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.engineering.ids import EngineeringSnapshotId
from codestrata_platform.domain.errors import InvalidStateTransitionError, InvalidValueError
from codestrata_platform.domain.knowledge_graph.identifiers import KnowledgeGraphId
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.retrieval.chunk import RetrievalChunk
from codestrata_platform.domain.retrieval.document import RetrievalDocument
from codestrata_platform.domain.retrieval.errors import RetrievalInvariantError
from codestrata_platform.domain.retrieval.identifiers import (
    EmbeddingDimension,
    EmbeddingModelId,
    EmbeddingProviderId,
    RetrievalIndexId,
    RetrievalProjectionKey,
)
from codestrata_platform.domain.retrieval.lifecycle import (
    RetrievalIndexStatus,
    RetrievalIndexVersion,
)
from codestrata_platform.domain.shared.audit import AuditInfo
from codestrata_platform.domain.workspace.ids import WorkspaceId


@dataclass(slots=True)
class EngineeringRetrievalIndex:
    """Rebuildable projection of Platform intelligence for retrieval."""

    index_id: RetrievalIndexId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    repository_id: RepositoryId
    assessment_id: AssessmentId
    engineering_snapshot_id: EngineeringSnapshotId
    engineering_snapshot_version: int
    knowledge_graph_id: KnowledgeGraphId
    knowledge_graph_version: int
    index_version: RetrievalIndexVersion
    status: RetrievalIndexStatus
    projection_key: RetrievalProjectionKey
    retrieval_schema_version: str
    chunking_policy_version: str
    embedding_provider_id: EmbeddingProviderId
    embedding_model_id: EmbeddingModelId
    embedding_dimension: EmbeddingDimension
    documents: tuple[RetrievalDocument, ...]
    chunks: tuple[RetrievalChunk, ...]
    audit: AuditInfo
    completed_at: datetime | None = None
    superseded_at: datetime | None = None
    failure_reason: str | None = None
    _version: int = field(default=0, repr=False)

    def __post_init__(self) -> None:
        self.retrieval_schema_version = self.retrieval_schema_version.strip()
        self.chunking_policy_version = self.chunking_policy_version.strip()
        if not self.retrieval_schema_version or not self.chunking_policy_version:
            raise InvalidValueError(
                "schema/chunking policy versions must be non-blank",
                reason_code="empty_retrieval_version",
            )
        self._assert_integrity()

    @classmethod
    def create_pending(
        cls,
        *,
        index_id: RetrievalIndexId,
        organization_id: OrganizationId,
        workspace_id: WorkspaceId,
        repository_id: RepositoryId,
        assessment_id: AssessmentId,
        engineering_snapshot_id: EngineeringSnapshotId,
        engineering_snapshot_version: int,
        knowledge_graph_id: KnowledgeGraphId,
        knowledge_graph_version: int,
        index_version: int,
        projection_key: RetrievalProjectionKey,
        retrieval_schema_version: str,
        chunking_policy_version: str,
        embedding_provider_id: EmbeddingProviderId,
        embedding_model_id: EmbeddingModelId,
        embedding_dimension: EmbeddingDimension,
    ) -> EngineeringRetrievalIndex:
        return cls(
            index_id=index_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            repository_id=repository_id,
            assessment_id=assessment_id,
            engineering_snapshot_id=engineering_snapshot_id,
            engineering_snapshot_version=engineering_snapshot_version,
            knowledge_graph_id=knowledge_graph_id,
            knowledge_graph_version=knowledge_graph_version,
            index_version=RetrievalIndexVersion(index_version),
            status=RetrievalIndexStatus.PENDING,
            projection_key=projection_key,
            retrieval_schema_version=retrieval_schema_version,
            chunking_policy_version=chunking_policy_version,
            embedding_provider_id=embedding_provider_id,
            embedding_model_id=embedding_model_id,
            embedding_dimension=embedding_dimension,
            documents=(),
            chunks=(),
            audit=AuditInfo.create(),
        )

    def begin_indexing(self) -> None:
        self._require_mutable()
        if self.status is not RetrievalIndexStatus.PENDING:
            raise InvalidStateTransitionError(
                f"Cannot begin indexing from status {self.status.value}",
                reason_code="invalid_begin_indexing",
            )
        self.status = RetrievalIndexStatus.INDEXING
        self.audit = self.audit.touch()
        self._version += 1

    def add_document(self, document: RetrievalDocument) -> None:
        self._require_indexing()
        if document.index_id != self.index_id:
            raise RetrievalInvariantError(
                "Document index_id mismatch",
                reason_code="document_index_mismatch",
            )
        existing = {item.document_id.value: item for item in self.documents}
        prior = existing.get(document.document_id.value)
        if prior is not None:
            if prior.checksum != document.checksum:
                raise RetrievalInvariantError(
                    "Conflicting document checksum",
                    reason_code="duplicate_document_conflict",
                )
            return
        self.documents = (*self.documents, document)
        self.audit = self.audit.touch()
        self._version += 1

    def add_chunk(self, chunk: RetrievalChunk) -> None:
        self._require_indexing()
        if chunk.index_id != self.index_id:
            raise RetrievalInvariantError(
                "Chunk index_id mismatch",
                reason_code="chunk_index_mismatch",
            )
        document_ids = {item.document_id.value for item in self.documents}
        if chunk.document_id.value not in document_ids:
            raise RetrievalInvariantError(
                "Chunk references unknown document",
                reason_code="chunk_document_missing",
            )
        if chunk.embedding is not None:
            if chunk.embedding.dimension != self.embedding_dimension.value:
                raise RetrievalInvariantError(
                    "Embedding dimension mismatch",
                    reason_code="embedding_dimension_mismatch",
                )
        for existing in self.chunks:
            if existing.chunk_id.value == chunk.chunk_id.value:
                if existing.checksum.value != chunk.checksum.value:
                    raise RetrievalInvariantError(
                        "Conflicting chunk checksum",
                        reason_code="duplicate_chunk_conflict",
                    )
                return
            if (
                existing.document_id == chunk.document_id
                and existing.checksum.value == chunk.checksum.value
            ):
                return
        self.chunks = (*self.chunks, chunk)
        self.audit = self.audit.touch()
        self._version += 1

    def complete(self) -> None:
        self._require_indexing()
        self._assert_integrity()
        if not self.documents or not self.chunks:
            raise RetrievalInvariantError(
                "Completed index requires documents and chunks",
                reason_code="empty_retrieval_index",
            )
        for chunk in self.chunks:
            if chunk.embedding is None:
                raise RetrievalInvariantError(
                    "All chunks must be embedded before completion",
                    reason_code="missing_chunk_embedding",
                )
        self.status = RetrievalIndexStatus.COMPLETED
        self.completed_at = datetime.now(UTC)
        self.failure_reason = None
        self.audit = self.audit.touch()
        self._version += 1

    def fail(self, reason: str) -> None:
        self._require_mutable()
        if self.status not in {
            RetrievalIndexStatus.PENDING,
            RetrievalIndexStatus.INDEXING,
        }:
            raise InvalidStateTransitionError(
                f"Cannot fail index in status {self.status.value}",
                reason_code="invalid_fail_transition",
            )
        compact = reason.strip()
        if not compact:
            raise InvalidValueError(
                "failure reason must be non-blank",
                reason_code="empty_failure_reason",
            )
        self.status = RetrievalIndexStatus.FAILED
        self.failure_reason = compact[:1000]
        self.documents = ()
        self.chunks = ()
        self.audit = self.audit.touch()
        self._version += 1

    def supersede(self) -> None:
        if self.status is not RetrievalIndexStatus.COMPLETED:
            raise InvalidStateTransitionError(
                f"Cannot supersede index in status {self.status.value}",
                reason_code="invalid_supersede_transition",
            )
        self.status = RetrievalIndexStatus.SUPERSEDED
        self.superseded_at = datetime.now(UTC)
        self.audit = self.audit.touch()
        self._version += 1

    def archive(self) -> None:
        if self.status not in {
            RetrievalIndexStatus.COMPLETED,
            RetrievalIndexStatus.SUPERSEDED,
        }:
            raise InvalidStateTransitionError(
                f"Cannot archive index in status {self.status.value}",
                reason_code="invalid_archive_transition",
            )
        self.status = RetrievalIndexStatus.ARCHIVED
        self.audit = self.audit.touch()
        self._version += 1

    def snapshot(self) -> EngineeringRetrievalIndex:
        return replace(self)

    def _require_mutable(self) -> None:
        if self.status is RetrievalIndexStatus.COMPLETED:
            raise InvalidStateTransitionError(
                "Completed retrieval indexes are immutable",
                reason_code="retrieval_index_immutable",
            )
        if self.status in {
            RetrievalIndexStatus.SUPERSEDED,
            RetrievalIndexStatus.ARCHIVED,
            RetrievalIndexStatus.FAILED,
        }:
            raise InvalidStateTransitionError(
                f"Index in status {self.status.value} is immutable",
                reason_code="retrieval_index_immutable",
            )

    def _require_indexing(self) -> None:
        self._require_mutable()
        if self.status is not RetrievalIndexStatus.INDEXING:
            raise InvalidStateTransitionError(
                f"Cannot mutate index contents in status {self.status.value}",
                reason_code="index_not_indexing",
            )

    def _assert_integrity(self) -> None:
        document_ids = [item.document_id.value for item in self.documents]
        if len(document_ids) != len(set(document_ids)):
            raise RetrievalInvariantError(
                "Document ids must be unique within an index",
                reason_code="duplicate_document_id",
            )
        chunk_ids = [item.chunk_id.value for item in self.chunks]
        if len(chunk_ids) != len(set(chunk_ids)):
            raise RetrievalInvariantError(
                "Chunk ids must be unique within an index",
                reason_code="duplicate_chunk_id",
            )
        known = set(document_ids)
        for chunk in self.chunks:
            if chunk.document_id.value not in known:
                raise RetrievalInvariantError(
                    "Chunks may only reference documents in the same index",
                    reason_code="chunk_document_mismatch",
                )
