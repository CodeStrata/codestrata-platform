"""EngineeringRetrievalIndex ↔ persistence record mapper."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.engineering.ids import EngineeringSnapshotId
from codestrata_platform.domain.knowledge_graph.identifiers import KnowledgeGraphId
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.retrieval.chunk import RetrievalChunk
from codestrata_platform.domain.retrieval.document import (
    RetrievalDocument,
    RetrievalSourceReference,
)
from codestrata_platform.domain.retrieval.identifiers import (
    ChunkChecksum,
    EmbeddingDimension,
    EmbeddingModelId,
    EmbeddingProviderId,
    EmbeddingVector,
    RetrievalChunkId,
    RetrievalDocumentId,
    RetrievalIndexId,
    RetrievalProjectionKey,
)
from codestrata_platform.domain.retrieval.index import EngineeringRetrievalIndex
from codestrata_platform.domain.retrieval.lifecycle import (
    RetrievalIndexStatus,
    RetrievalIndexVersion,
)
from codestrata_platform.domain.retrieval.taxonomy import RetrievalContentType
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.infrastructure.persistence.mappers._helpers import (
    audit_from_record,
    ensure_utc,
)
from codestrata_platform.infrastructure.persistence.models.retrieval_records import (
    EngineeringRetrievalChunkRecord,
    EngineeringRetrievalDocumentRecord,
    EngineeringRetrievalIndexRecord,
)


def _source_refs_to_json(
    refs: tuple[RetrievalSourceReference, ...],
) -> list[dict[str, Any]]:
    return [
        {
            "source_kind": item.source_kind,
            "source_id": item.source_id,
            "snapshot_id": item.snapshot_id,
            "graph_id": item.graph_id,
        }
        for item in refs
    ]


def _source_refs_from_json(
    raw: list[dict[str, Any]] | None,
) -> tuple[RetrievalSourceReference, ...]:
    if not raw:
        return ()
    return tuple(
        RetrievalSourceReference(
            source_kind=str(item.get("source_kind", "")),
            source_id=str(item.get("source_id", "")),
            snapshot_id=item.get("snapshot_id"),
            graph_id=item.get("graph_id"),
        )
        for item in raw
    )


class RetrievalIndexMapper:
    @staticmethod
    def to_record(index: EngineeringRetrievalIndex) -> EngineeringRetrievalIndexRecord:
        return EngineeringRetrievalIndexRecord(
            id=index.index_id.value,
            organization_id=index.organization_id.value,
            workspace_id=index.workspace_id.value,
            repository_id=index.repository_id.value,
            assessment_id=index.assessment_id.value,
            engineering_snapshot_id=index.engineering_snapshot_id.value,
            engineering_snapshot_version=index.engineering_snapshot_version,
            knowledge_graph_id=index.knowledge_graph_id.value,
            knowledge_graph_version=index.knowledge_graph_version,
            index_version=index.index_version.value,
            status=index.status.value,
            retrieval_schema_version=index.retrieval_schema_version,
            chunking_policy_version=index.chunking_policy_version,
            embedding_provider_id=index.embedding_provider_id.value,
            embedding_model_id=index.embedding_model_id.value,
            embedding_dimension=index.embedding_dimension.value,
            projection_key=index.projection_key.value,
            created_at=index.audit.created_at.value,
            updated_at=index.audit.updated_at.value,
            completed_at=index.completed_at,
            superseded_at=index.superseded_at,
            failure_reason=index.failure_reason,
            optimistic_version=index._version,
        )

    @staticmethod
    def apply_to_record(
        index: EngineeringRetrievalIndex,
        record: EngineeringRetrievalIndexRecord,
    ) -> None:
        record.organization_id = index.organization_id.value
        record.workspace_id = index.workspace_id.value
        record.repository_id = index.repository_id.value
        record.assessment_id = index.assessment_id.value
        record.engineering_snapshot_id = index.engineering_snapshot_id.value
        record.engineering_snapshot_version = index.engineering_snapshot_version
        record.knowledge_graph_id = index.knowledge_graph_id.value
        record.knowledge_graph_version = index.knowledge_graph_version
        record.index_version = index.index_version.value
        record.status = index.status.value
        record.retrieval_schema_version = index.retrieval_schema_version
        record.chunking_policy_version = index.chunking_policy_version
        record.embedding_provider_id = index.embedding_provider_id.value
        record.embedding_model_id = index.embedding_model_id.value
        record.embedding_dimension = index.embedding_dimension.value
        record.projection_key = index.projection_key.value
        record.created_at = index.audit.created_at.value
        record.updated_at = index.audit.updated_at.value
        record.completed_at = index.completed_at
        record.superseded_at = index.superseded_at
        record.failure_reason = index.failure_reason
        record.optimistic_version = index._version

    @staticmethod
    def to_document_record(
        document: RetrievalDocument,
        *,
        created_at: datetime | None = None,
    ) -> EngineeringRetrievalDocumentRecord:
        return EngineeringRetrievalDocumentRecord(
            id=document.document_id.value,
            index_id=document.index_id.value,
            content_type=document.content_type.value,
            canonical_type=document.canonical_type,
            canonical_id=document.canonical_id,
            title=document.title,
            summary=document.summary,
            structured_content=dict(document.structured_content),
            source_references=_source_refs_to_json(document.source_references),
            graph_node_ids=list(document.graph_node_ids),
            graph_edge_ids=list(document.graph_edge_ids),
            metadata_json=dict(document.metadata),
            checksum=document.checksum,
            created_at=created_at or datetime.now(UTC),
        )

    @staticmethod
    def to_chunk_record(
        chunk: RetrievalChunk,
        *,
        created_at: datetime | None = None,
    ) -> EngineeringRetrievalChunkRecord:
        return EngineeringRetrievalChunkRecord(
            id=chunk.chunk_id.value,
            document_id=chunk.document_id.value,
            index_id=chunk.index_id.value,
            ordinal=chunk.ordinal,
            text=chunk.text,
            token_estimate=chunk.token_estimate,
            checksum=chunk.checksum.value,
            embedding=list(chunk.embedding.values) if chunk.embedding is not None else None,
            search_vector_text=chunk.text,
            source_references=_source_refs_to_json(chunk.source_references),
            graph_node_ids=list(chunk.graph_node_ids),
            graph_edge_ids=list(chunk.graph_edge_ids),
            metadata_json=dict(chunk.metadata),
            created_at=created_at or datetime.now(UTC),
        )

    @staticmethod
    def to_domain(
        record: EngineeringRetrievalIndexRecord,
        documents: list[EngineeringRetrievalDocumentRecord],
        chunks: list[EngineeringRetrievalChunkRecord],
    ) -> EngineeringRetrievalIndex:
        domain_documents = tuple(
            RetrievalDocument(
                document_id=RetrievalDocumentId(item.id),
                index_id=RetrievalIndexId(item.index_id),
                content_type=RetrievalContentType(item.content_type),
                canonical_type=item.canonical_type,
                canonical_id=item.canonical_id,
                title=item.title,
                summary=item.summary,
                structured_content=dict(item.structured_content or {}),
                source_references=_source_refs_from_json(item.source_references),
                graph_node_ids=tuple(item.graph_node_ids or ()),
                graph_edge_ids=tuple(item.graph_edge_ids or ()),
                metadata=dict(item.metadata_json or {}),
                checksum=item.checksum,
            )
            for item in sorted(documents, key=lambda row: row.id)
        )
        domain_chunks = tuple(
            RetrievalChunk(
                chunk_id=RetrievalChunkId(item.id),
                document_id=RetrievalDocumentId(item.document_id),
                index_id=RetrievalIndexId(item.index_id),
                ordinal=item.ordinal,
                text=item.text,
                token_estimate=item.token_estimate,
                checksum=ChunkChecksum(item.checksum),
                embedding=(
                    EmbeddingVector(tuple(float(v) for v in item.embedding))
                    if item.embedding is not None
                    else None
                ),
                source_references=_source_refs_from_json(item.source_references),
                graph_node_ids=tuple(item.graph_node_ids or ()),
                graph_edge_ids=tuple(item.graph_edge_ids or ()),
                metadata=dict(item.metadata_json or {}),
            )
            for item in sorted(chunks, key=lambda row: (row.ordinal, row.id))
        )
        return EngineeringRetrievalIndex(
            index_id=RetrievalIndexId(record.id),
            organization_id=OrganizationId(record.organization_id),
            workspace_id=WorkspaceId(record.workspace_id),
            repository_id=RepositoryId(record.repository_id),
            assessment_id=AssessmentId(record.assessment_id),
            engineering_snapshot_id=EngineeringSnapshotId(record.engineering_snapshot_id),
            engineering_snapshot_version=record.engineering_snapshot_version,
            knowledge_graph_id=KnowledgeGraphId(record.knowledge_graph_id),
            knowledge_graph_version=record.knowledge_graph_version,
            index_version=RetrievalIndexVersion(record.index_version),
            status=RetrievalIndexStatus(record.status),
            projection_key=RetrievalProjectionKey(record.projection_key),
            retrieval_schema_version=record.retrieval_schema_version,
            chunking_policy_version=record.chunking_policy_version,
            embedding_provider_id=EmbeddingProviderId(record.embedding_provider_id),
            embedding_model_id=EmbeddingModelId(record.embedding_model_id),
            embedding_dimension=EmbeddingDimension(record.embedding_dimension),
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
