"""Domain tests for Portfolio Retrieval Index."""

from __future__ import annotations

import pytest

from codestrata_platform.domain.errors import InvalidStateTransitionError, InvalidValueError
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.portfolio_retrieval.chunk import PortfolioRetrievalChunk
from codestrata_platform.domain.portfolio_retrieval.citation import PortfolioRetrievalCitation
from codestrata_platform.domain.portfolio_retrieval.document import PortfolioRetrievalDocument
from codestrata_platform.domain.portfolio_retrieval.errors import PortfolioRetrievalInvariantError
from codestrata_platform.domain.portfolio_retrieval.identifiers import (
    ChunkChecksum,
    EmbeddingDimension,
    EmbeddingModelId,
    EmbeddingProviderId,
    EmbeddingVector,
    PortfolioRetrievalProjectionKey,
    deterministic_portfolio_chunk_id,
    deterministic_portfolio_document_id,
    deterministic_portfolio_index_id,
)
from codestrata_platform.domain.portfolio_retrieval.index import PortfolioRetrievalIndex
from codestrata_platform.domain.portfolio_retrieval.lifecycle import PortfolioRetrievalIndexStatus
from codestrata_platform.domain.portfolio_retrieval.taxonomy import PortfolioRetrievalContentType
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId


def _citation() -> PortfolioRetrievalCitation:
    return PortfolioRetrievalCitation(
        source_kind="portfolio_snapshot",
        source_id="portfolio-snapshot:1",
        portfolio_snapshot_id="portfolio-snapshot:1",
    )


def _pending_index() -> PortfolioRetrievalIndex:
    projection = PortfolioRetrievalProjectionKey.from_parts(
        portfolio_id="portfolio:1",
        portfolio_snapshot_id="portfolio-snapshot:1",
        portfolio_snapshot_version=1,
        selected_repository_snapshot_identities=("repo:1:eng-snapshot:1:1::0",),
        retrieval_schema_version="1.0",
        chunking_policy_version="1.0.0",
        ranking_policy_version="1.0.0",
        embedding_provider_id="deterministic",
        embedding_model_id="deterministic-test-embedding",
        embedding_dimension=384,
    )
    return PortfolioRetrievalIndex.create_pending(
        index_id=deterministic_portfolio_index_id(
            portfolio_id="portfolio:1",
            portfolio_snapshot_id="portfolio-snapshot:1",
            projection_key=projection.value,
        ),
        organization_id=OrganizationId("org:1"),
        workspace_id=WorkspaceId("workspace:1"),
        portfolio_id=PortfolioId("portfolio:1"),
        portfolio_snapshot_id=PortfolioSnapshotId("portfolio-snapshot:1"),
        portfolio_snapshot_version=1,
        index_version=1,
        projection_key=projection,
        retrieval_schema_version="1.0",
        chunking_policy_version="1.0.0",
        ranking_policy_version="1.0.0",
        embedding_provider_id=EmbeddingProviderId("deterministic"),
        embedding_model_id=EmbeddingModelId("deterministic-test-embedding"),
        embedding_dimension=EmbeddingDimension(384),
        repository_ids=(RepositoryId("repo:1"),),
    )


def _document(index: PortfolioRetrievalIndex) -> PortfolioRetrievalDocument:
    return PortfolioRetrievalDocument(
        document_id=deterministic_portfolio_document_id(
            index_id=index.index_id.value,
            content_type=PortfolioRetrievalContentType.PORTFOLIO_SUMMARY.value,
            canonical_id="portfolio:1",
        ),
        index_id=index.index_id,
        portfolio_id=index.portfolio_id,
        portfolio_snapshot_id=index.portfolio_snapshot_id,
        content_type=PortfolioRetrievalContentType.PORTFOLIO_SUMMARY,
        canonical_type="portfolio",
        canonical_id="portfolio:1",
        title="Portfolio overview",
        summary="Portfolio summary with debt and modernization signals.",
        citations=(_citation(),),
    )


def _chunk(
    index: PortfolioRetrievalIndex,
    document: PortfolioRetrievalDocument,
) -> PortfolioRetrievalChunk:
    text = "Portfolio overview. Debt hotspot across repositories. Modernization candidates."
    checksum = ChunkChecksum.from_text(text)
    return PortfolioRetrievalChunk(
        chunk_id=deterministic_portfolio_chunk_id(
            document_id=document.document_id.value,
            ordinal=0,
            checksum=checksum.value,
        ),
        document_id=document.document_id,
        index_id=index.index_id,
        portfolio_id=index.portfolio_id,
        portfolio_snapshot_id=index.portfolio_snapshot_id,
        ordinal=0,
        text=text,
        token_estimate=0,
        checksum=checksum,
        repository_ids=(RepositoryId("repo:1"),),
        primary_repository_id=RepositoryId("repo:1"),
        citations=(_citation(),),
        embedding=EmbeddingVector(values=tuple([0.1] * 384)),
    )


def test_index_lifecycle_complete_and_immutable() -> None:
    index = _pending_index()
    assert index.status is PortfolioRetrievalIndexStatus.PENDING
    index.begin_indexing()
    document = _document(index)
    index.add_document(document)
    index.add_chunk(_chunk(index, document))
    index.complete()
    assert index.status is PortfolioRetrievalIndexStatus.COMPLETED
    with pytest.raises(InvalidStateTransitionError):
        index.begin_indexing()
    with pytest.raises((InvalidStateTransitionError, PortfolioRetrievalInvariantError)):
        index.add_document(document)


def test_projection_key_is_deterministic() -> None:
    first = PortfolioRetrievalProjectionKey.from_parts(
        portfolio_id="portfolio:1",
        portfolio_snapshot_id="portfolio-snapshot:1",
        portfolio_snapshot_version=1,
        selected_repository_snapshot_identities=("b", "a"),
        retrieval_schema_version="1.0",
        chunking_policy_version="1.0.0",
        ranking_policy_version="1.0.0",
        embedding_provider_id="deterministic",
        embedding_model_id="deterministic-test-embedding",
        embedding_dimension=384,
    )
    second = PortfolioRetrievalProjectionKey.from_parts(
        portfolio_id="portfolio:1",
        portfolio_snapshot_id="portfolio-snapshot:1",
        portfolio_snapshot_version=1,
        selected_repository_snapshot_identities=("a", "b"),
        retrieval_schema_version="1.0",
        chunking_policy_version="1.0.0",
        ranking_policy_version="1.0.0",
        embedding_provider_id="deterministic",
        embedding_model_id="deterministic-test-embedding",
        embedding_dimension=384,
    )
    assert first.value == second.value


def test_document_requires_citations() -> None:
    index = _pending_index()
    with pytest.raises(InvalidValueError):
        PortfolioRetrievalDocument(
            document_id=deterministic_portfolio_document_id(
                index_id=index.index_id.value,
                content_type=PortfolioRetrievalContentType.PORTFOLIO_SUMMARY.value,
                canonical_id="portfolio:1",
            ),
            index_id=index.index_id,
            portfolio_id=index.portfolio_id,
            portfolio_snapshot_id=index.portfolio_snapshot_id,
            content_type=PortfolioRetrievalContentType.PORTFOLIO_SUMMARY,
            canonical_type="portfolio",
            canonical_id="portfolio:1",
            title="Portfolio overview",
            summary="Summary",
            citations=(),
        )


def test_supersede_completed_index() -> None:
    index = _pending_index()
    index.begin_indexing()
    document = _document(index)
    index.add_document(document)
    index.add_chunk(_chunk(index, document))
    index.complete()
    index.supersede()
    assert index.status is PortfolioRetrievalIndexStatus.SUPERSEDED
