"""Domain tests for Engineering Retrieval Index."""

from __future__ import annotations

import pytest

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.engineering.ids import EngineeringSnapshotId
from codestrata_platform.domain.errors import InvalidStateTransitionError, InvalidValueError
from codestrata_platform.domain.knowledge_graph.identifiers import KnowledgeGraphId
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.retrieval.chunk import RetrievalChunk, estimate_tokens
from codestrata_platform.domain.retrieval.document import (
    RetrievalDocument,
    RetrievalSourceReference,
)
from codestrata_platform.domain.retrieval.errors import RetrievalInvariantError
from codestrata_platform.domain.retrieval.identifiers import (
    ChunkChecksum,
    EmbeddingDimension,
    EmbeddingModelId,
    EmbeddingProviderId,
    EmbeddingVector,
    RetrievalProjectionKey,
    deterministic_chunk_id,
    deterministic_document_id,
    deterministic_index_id,
)
from codestrata_platform.domain.retrieval.index import EngineeringRetrievalIndex
from codestrata_platform.domain.retrieval.lifecycle import RetrievalIndexStatus
from codestrata_platform.domain.retrieval.taxonomy import RetrievalContentType
from codestrata_platform.domain.workspace.ids import WorkspaceId


def _ref() -> RetrievalSourceReference:
    return RetrievalSourceReference(
        source_kind="engineering_snapshot",
        source_id="eng-snapshot:1",
        snapshot_id="eng-snapshot:1",
    )


def _pending_index() -> EngineeringRetrievalIndex:
    projection = RetrievalProjectionKey.from_parts(
        engineering_snapshot_id="eng-snapshot:1",
        engineering_snapshot_version=1,
        knowledge_graph_id="eng-graph:1",
        knowledge_graph_version=1,
        retrieval_schema_version="1.0",
        chunking_policy_version="1.0.0",
        embedding_provider_id="deterministic",
        embedding_model_id="deterministic-test-embedding",
        embedding_dimension=384,
    )
    return EngineeringRetrievalIndex.create_pending(
        index_id=deterministic_index_id(
            repository_id="repo:1",
            snapshot_id="eng-snapshot:1",
            graph_id="eng-graph:1",
            projection_key=projection.value,
        ),
        organization_id=OrganizationId("org:1"),
        workspace_id=WorkspaceId("workspace:1"),
        repository_id=RepositoryId("repo:1"),
        assessment_id=AssessmentId("assessment:1"),
        engineering_snapshot_id=EngineeringSnapshotId("eng-snapshot:1"),
        engineering_snapshot_version=1,
        knowledge_graph_id=KnowledgeGraphId("eng-graph:1"),
        knowledge_graph_version=1,
        index_version=1,
        projection_key=projection,
        retrieval_schema_version="1.0",
        chunking_policy_version="1.0.0",
        embedding_provider_id=EmbeddingProviderId("deterministic"),
        embedding_model_id=EmbeddingModelId("deterministic-test-embedding"),
        embedding_dimension=EmbeddingDimension(384),
    )


def _document(index: EngineeringRetrievalIndex) -> RetrievalDocument:
    return RetrievalDocument(
        document_id=deterministic_document_id(
            index_id=index.index_id.value,
            content_type=RetrievalContentType.FINDING.value,
            canonical_id="finding:1",
        ),
        index_id=index.index_id,
        content_type=RetrievalContentType.FINDING,
        canonical_type="finding",
        canonical_id="finding:1",
        title="Privileged container",
        summary="Container runs privileged.",
        structured_content={"severity": "critical"},
        source_references=(_ref(),),
    )


def _chunk(index: EngineeringRetrievalIndex, document: RetrievalDocument) -> RetrievalChunk:
    text = "Finding Privileged container. Severity critical."
    checksum = ChunkChecksum.from_text(text)
    return RetrievalChunk(
        chunk_id=deterministic_chunk_id(
            document_id=document.document_id.value,
            ordinal=0,
            checksum=checksum.value,
        ),
        document_id=document.document_id,
        index_id=index.index_id,
        ordinal=0,
        text=text,
        token_estimate=estimate_tokens(text),
        checksum=checksum,
        embedding=EmbeddingVector(tuple(0.0 for _ in range(383)) + (1.0,)),
        source_references=document.source_references,
    )


def test_retrieval_index_lifecycle_and_immutability() -> None:
    index = _pending_index()
    index.begin_indexing()
    document = _document(index)
    chunk = _chunk(index, document)
    index.add_document(document)
    index.add_chunk(chunk)
    index.complete()
    assert index.status is RetrievalIndexStatus.COMPLETED
    with pytest.raises(InvalidStateTransitionError):
        index.add_document(document)
    index.supersede()
    assert index.status is RetrievalIndexStatus.SUPERSEDED
    index.archive()
    assert index.status is RetrievalIndexStatus.ARCHIVED


def test_embedding_vector_validation() -> None:
    with pytest.raises(InvalidValueError):
        EmbeddingVector((1.0, float("nan")))
    with pytest.raises(InvalidValueError):
        EmbeddingVector((1.0, float("inf")))
    vector = EmbeddingVector((0.0, 1.0))
    assert vector.dimension == 2
    assert all(
        value == value and value not in {float("inf"), float("-inf")} for value in vector.values
    )


def test_deterministic_checksums_and_projection_key() -> None:
    index = _pending_index()
    document = _document(index)
    again = _document(index)
    assert document.checksum == again.checksum
    text = "same chunk text"
    assert ChunkChecksum.from_text(text) == ChunkChecksum.from_text(text)
    key_a = RetrievalProjectionKey.from_parts(
        engineering_snapshot_id="s",
        engineering_snapshot_version=1,
        knowledge_graph_id="g",
        knowledge_graph_version=1,
        retrieval_schema_version="1.0",
        chunking_policy_version="1.0.0",
        embedding_provider_id="deterministic",
        embedding_model_id="m",
        embedding_dimension=384,
    )
    key_b = RetrievalProjectionKey.from_parts(
        engineering_snapshot_id="s",
        engineering_snapshot_version=1,
        knowledge_graph_id="g",
        knowledge_graph_version=1,
        retrieval_schema_version="1.0",
        chunking_policy_version="1.0.0",
        embedding_provider_id="deterministic",
        embedding_model_id="m",
        embedding_dimension=384,
    )
    assert key_a.value == key_b.value


def test_duplicate_chunk_checksum_is_idempotent() -> None:
    index = _pending_index()
    index.begin_indexing()
    document = _document(index)
    chunk = _chunk(index, document)
    index.add_document(document)
    index.add_chunk(chunk)
    index.add_chunk(chunk)
    assert len(index.chunks) == 1


def test_document_requires_source_references() -> None:
    index = _pending_index()
    with pytest.raises(InvalidValueError):
        RetrievalDocument(
            document_id=deterministic_document_id(
                index_id=index.index_id.value,
                content_type=RetrievalContentType.METRIC.value,
                canonical_id="metric:1",
            ),
            index_id=index.index_id,
            content_type=RetrievalContentType.METRIC,
            canonical_type="metric",
            canonical_id="metric:1",
            title="count",
            summary="Metric count",
            source_references=(),
        )


def test_embedding_dimension_mismatch_rejected() -> None:
    index = _pending_index()
    index.begin_indexing()
    document = _document(index)
    index.add_document(document)
    text = "Finding Privileged container. Severity critical."
    checksum = ChunkChecksum.from_text(text)
    bad = RetrievalChunk(
        chunk_id=deterministic_chunk_id(
            document_id=document.document_id.value,
            ordinal=0,
            checksum=checksum.value,
        ),
        document_id=document.document_id,
        index_id=index.index_id,
        ordinal=0,
        text=text,
        token_estimate=estimate_tokens(text),
        checksum=checksum,
        embedding=EmbeddingVector((1.0, 0.0)),
        source_references=document.source_references,
    )
    with pytest.raises(RetrievalInvariantError):
        index.add_chunk(bad)
