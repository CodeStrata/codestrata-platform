"""PortfolioRetrievalIndex ↔ persistence record mapper."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.portfolio_retrieval.chunk import PortfolioRetrievalChunk
from codestrata_platform.domain.portfolio_retrieval.citation import PortfolioRetrievalCitation
from codestrata_platform.domain.portfolio_retrieval.document import PortfolioRetrievalDocument
from codestrata_platform.domain.portfolio_retrieval.identifiers import (
    ChunkChecksum,
    EmbeddingDimension,
    EmbeddingModelId,
    EmbeddingProviderId,
    EmbeddingVector,
    PortfolioRetrievalChunkId,
    PortfolioRetrievalDocumentId,
    PortfolioRetrievalIndexId,
    PortfolioRetrievalProjectionKey,
)
from codestrata_platform.domain.portfolio_retrieval.index import PortfolioRetrievalIndex
from codestrata_platform.domain.portfolio_retrieval.lifecycle import (
    PortfolioRetrievalIndexStatus,
    PortfolioRetrievalIndexVersion,
)
from codestrata_platform.domain.portfolio_retrieval.taxonomy import PortfolioRetrievalContentType
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.infrastructure.persistence.mappers._helpers import (
    audit_from_record,
    ensure_utc,
)
from codestrata_platform.infrastructure.persistence.models.portfolio_retrieval_records import (
    EngineeringPortfolioRetrievalChunkRecord,
    EngineeringPortfolioRetrievalDocumentRecord,
    EngineeringPortfolioRetrievalIndexRecord,
)


def _citations_to_json(
    citations: tuple[PortfolioRetrievalCitation, ...],
) -> list[dict[str, Any]]:
    return [
        {
            "source_kind": item.source_kind,
            "source_id": item.source_id,
            "repository_id": item.repository_id,
            "engineering_snapshot_id": item.engineering_snapshot_id,
            "portfolio_snapshot_id": item.portfolio_snapshot_id,
        }
        for item in citations
    ]


def _citations_from_json(
    raw: list[dict[str, Any]] | None,
) -> tuple[PortfolioRetrievalCitation, ...]:
    if not raw:
        return ()
    return tuple(
        PortfolioRetrievalCitation(
            source_kind=str(item.get("source_kind", "")),
            source_id=str(item.get("source_id", "")),
            repository_id=item.get("repository_id"),
            engineering_snapshot_id=item.get("engineering_snapshot_id"),
            portfolio_snapshot_id=item.get("portfolio_snapshot_id"),
        )
        for item in raw
    )


class PortfolioRetrievalIndexMapper:
    @staticmethod
    def to_record(index: PortfolioRetrievalIndex) -> EngineeringPortfolioRetrievalIndexRecord:
        return EngineeringPortfolioRetrievalIndexRecord(
            id=index.index_id.value,
            organization_id=index.organization_id.value,
            workspace_id=index.workspace_id.value,
            portfolio_id=index.portfolio_id.value,
            portfolio_snapshot_id=index.portfolio_snapshot_id.value,
            portfolio_snapshot_version=index.portfolio_snapshot_version,
            index_version=index.index_version.value,
            status=index.status.value,
            retrieval_schema_version=index.retrieval_schema_version,
            chunking_policy_version=index.chunking_policy_version,
            ranking_policy_version=index.ranking_policy_version,
            embedding_provider_id=index.embedding_provider_id.value,
            embedding_model_id=index.embedding_model_id.value,
            embedding_dimension=index.embedding_dimension.value,
            projection_key=index.projection_key.value,
            repository_ids=[item.value for item in index.repository_ids],
            created_at=index.audit.created_at.value,
            updated_at=index.audit.updated_at.value,
            completed_at=index.completed_at,
            superseded_at=index.superseded_at,
            failure_reason=index.failure_reason,
            optimistic_version=index._version,  # noqa: SLF001
        )

    @staticmethod
    def apply_to_record(
        index: PortfolioRetrievalIndex,
        record: EngineeringPortfolioRetrievalIndexRecord,
    ) -> None:
        record.organization_id = index.organization_id.value
        record.workspace_id = index.workspace_id.value
        record.portfolio_id = index.portfolio_id.value
        record.portfolio_snapshot_id = index.portfolio_snapshot_id.value
        record.portfolio_snapshot_version = index.portfolio_snapshot_version
        record.index_version = index.index_version.value
        record.status = index.status.value
        record.retrieval_schema_version = index.retrieval_schema_version
        record.chunking_policy_version = index.chunking_policy_version
        record.ranking_policy_version = index.ranking_policy_version
        record.embedding_provider_id = index.embedding_provider_id.value
        record.embedding_model_id = index.embedding_model_id.value
        record.embedding_dimension = index.embedding_dimension.value
        record.projection_key = index.projection_key.value
        record.repository_ids = [item.value for item in index.repository_ids]
        record.created_at = index.audit.created_at.value
        record.updated_at = index.audit.updated_at.value
        record.completed_at = index.completed_at
        record.superseded_at = index.superseded_at
        record.failure_reason = index.failure_reason
        record.optimistic_version = index._version  # noqa: SLF001

    @staticmethod
    def to_document_record(
        document: PortfolioRetrievalDocument,
        *,
        created_at: datetime | None = None,
    ) -> EngineeringPortfolioRetrievalDocumentRecord:
        return EngineeringPortfolioRetrievalDocumentRecord(
            id=document.document_id.value,
            index_id=document.index_id.value,
            portfolio_id=document.portfolio_id.value,
            portfolio_snapshot_id=document.portfolio_snapshot_id.value,
            content_type=document.content_type.value,
            canonical_type=document.canonical_type,
            canonical_id=document.canonical_id,
            title=document.title,
            summary=document.summary,
            repository_ids=[item.value for item in document.repository_ids],
            primary_repository_id=(
                document.primary_repository_id.value
                if document.primary_repository_id is not None
                else None
            ),
            structured_content=dict(document.structured_content),
            citations=_citations_to_json(document.citations),
            metadata_json=dict(document.metadata),
            checksum=document.checksum,
            created_at=created_at or datetime.now(UTC),
        )

    @staticmethod
    def to_chunk_record(
        chunk: PortfolioRetrievalChunk,
        *,
        created_at: datetime | None = None,
    ) -> EngineeringPortfolioRetrievalChunkRecord:
        return EngineeringPortfolioRetrievalChunkRecord(
            id=chunk.chunk_id.value,
            document_id=chunk.document_id.value,
            index_id=chunk.index_id.value,
            portfolio_id=chunk.portfolio_id.value,
            portfolio_snapshot_id=chunk.portfolio_snapshot_id.value,
            ordinal=chunk.ordinal,
            text=chunk.text,
            token_estimate=chunk.token_estimate,
            checksum=chunk.checksum.value,
            repository_ids=[item.value for item in chunk.repository_ids],
            primary_repository_id=(
                chunk.primary_repository_id.value
                if chunk.primary_repository_id is not None
                else None
            ),
            embedding=list(chunk.embedding.values) if chunk.embedding is not None else None,
            search_vector_text=chunk.text,
            citations=_citations_to_json(chunk.citations),
            metadata_json=dict(chunk.metadata),
            created_at=created_at or datetime.now(UTC),
        )

    @staticmethod
    def to_domain(
        record: EngineeringPortfolioRetrievalIndexRecord,
        documents: list[EngineeringPortfolioRetrievalDocumentRecord],
        chunks: list[EngineeringPortfolioRetrievalChunkRecord],
    ) -> PortfolioRetrievalIndex:
        domain_documents = tuple(
            PortfolioRetrievalDocument(
                document_id=PortfolioRetrievalDocumentId(item.id),
                index_id=PortfolioRetrievalIndexId(item.index_id),
                portfolio_id=PortfolioId(item.portfolio_id),
                portfolio_snapshot_id=PortfolioSnapshotId(item.portfolio_snapshot_id),
                content_type=PortfolioRetrievalContentType(item.content_type),
                canonical_type=item.canonical_type,
                canonical_id=item.canonical_id,
                title=item.title,
                summary=item.summary,
                repository_ids=tuple(RepositoryId(value) for value in item.repository_ids or ()),
                primary_repository_id=(
                    RepositoryId(item.primary_repository_id)
                    if item.primary_repository_id is not None
                    else None
                ),
                structured_content=dict(item.structured_content or {}),
                citations=_citations_from_json(item.citations),
                metadata=dict(item.metadata_json or {}),
                checksum=item.checksum,
            )
            for item in sorted(documents, key=lambda row: row.id)
        )
        domain_chunks = tuple(
            PortfolioRetrievalChunk(
                chunk_id=PortfolioRetrievalChunkId(item.id),
                document_id=PortfolioRetrievalDocumentId(item.document_id),
                index_id=PortfolioRetrievalIndexId(item.index_id),
                portfolio_id=PortfolioId(item.portfolio_id),
                portfolio_snapshot_id=PortfolioSnapshotId(item.portfolio_snapshot_id),
                ordinal=item.ordinal,
                text=item.text,
                token_estimate=item.token_estimate,
                checksum=ChunkChecksum(item.checksum),
                repository_ids=tuple(RepositoryId(value) for value in item.repository_ids or ()),
                primary_repository_id=(
                    RepositoryId(item.primary_repository_id)
                    if item.primary_repository_id is not None
                    else None
                ),
                embedding=(
                    EmbeddingVector(tuple(float(v) for v in item.embedding))
                    if item.embedding is not None
                    else None
                ),
                citations=_citations_from_json(item.citations),
                metadata=dict(item.metadata_json or {}),
            )
            for item in sorted(chunks, key=lambda row: (row.ordinal, row.id))
        )
        return PortfolioRetrievalIndex(
            index_id=PortfolioRetrievalIndexId(record.id),
            organization_id=OrganizationId(record.organization_id),
            workspace_id=WorkspaceId(record.workspace_id),
            portfolio_id=PortfolioId(record.portfolio_id),
            portfolio_snapshot_id=PortfolioSnapshotId(record.portfolio_snapshot_id),
            portfolio_snapshot_version=record.portfolio_snapshot_version,
            index_version=PortfolioRetrievalIndexVersion(record.index_version),
            status=PortfolioRetrievalIndexStatus(record.status),
            projection_key=PortfolioRetrievalProjectionKey(record.projection_key),
            retrieval_schema_version=record.retrieval_schema_version,
            chunking_policy_version=record.chunking_policy_version,
            ranking_policy_version=record.ranking_policy_version,
            embedding_provider_id=EmbeddingProviderId(record.embedding_provider_id),
            embedding_model_id=EmbeddingModelId(record.embedding_model_id),
            embedding_dimension=EmbeddingDimension(record.embedding_dimension),
            repository_ids=tuple(RepositoryId(value) for value in record.repository_ids or ()),
            documents=domain_documents,
            chunks=domain_chunks,
            audit=audit_from_record(
                created_at=record.created_at,
                updated_at=record.updated_at,
            ),
            completed_at=ensure_utc(record.completed_at) if record.completed_at else None,
            superseded_at=ensure_utc(record.superseded_at) if record.superseded_at else None,
            failure_reason=record.failure_reason,
            _version=record.optimistic_version,
        )
