"""SqlAlchemy Portfolio Retrieval Index repository."""

from __future__ import annotations

from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from codestrata_platform.domain.portfolio.identifiers import PortfolioId
from codestrata_platform.domain.portfolio.lifecycle import RepositoryCriticality
from codestrata_platform.domain.portfolio_retrieval.chunk import PortfolioRetrievalChunk
from codestrata_platform.domain.portfolio_retrieval.document import PortfolioRetrievalDocument
from codestrata_platform.domain.portfolio_retrieval.identifiers import (
    PortfolioRetrievalChunkId,
    PortfolioRetrievalDocumentId,
    PortfolioRetrievalIndexId,
)
from codestrata_platform.domain.portfolio_retrieval.index import PortfolioRetrievalIndex
from codestrata_platform.domain.portfolio_retrieval.lifecycle import PortfolioRetrievalIndexStatus
from codestrata_platform.domain.portfolio_retrieval.query import PortfolioRetrievalQuery
from codestrata_platform.domain.portfolio_retrieval.result import PortfolioRetrievalSearchResult
from codestrata_platform.domain.portfolio_retrieval.scope import PortfolioRetrievalScope
from codestrata_platform.domain.retrieval.embedding import EmbeddingProvider
from codestrata_platform.domain.retrieval.taxonomy import RetrievalMode
from codestrata_platform.infrastructure.persistence.mappers.portfolio_retrieval_mapper import (
    PortfolioRetrievalIndexMapper,
)
from codestrata_platform.infrastructure.persistence.models.portfolio_retrieval_records import (
    EngineeringPortfolioRetrievalChunkRecord,
    EngineeringPortfolioRetrievalDocumentRecord,
    EngineeringPortfolioRetrievalIndexRecord,
)
from codestrata_platform.infrastructure.portfolio_retrieval.search import search_portfolio_index

_COMPLETED_ALLOWED_TRANSITIONS = frozenset(
    {
        PortfolioRetrievalIndexStatus.COMPLETED,
        PortfolioRetrievalIndexStatus.SUPERSEDED,
        PortfolioRetrievalIndexStatus.ARCHIVED,
    }
)


class SqlAlchemyPortfolioRetrievalRepository:
    """Durable PortfolioRetrievalIndexRepository + PortfolioRetrievalQueryRepository adapter."""

    def __init__(
        self,
        session: Session,
        *,
        embeddings: EmbeddingProvider | None = None,
    ) -> None:
        self._session = session
        self._embeddings = embeddings

    def get(self, index_id: PortfolioRetrievalIndexId) -> PortfolioRetrievalIndex | None:
        record = self._session.get(EngineeringPortfolioRetrievalIndexRecord, index_id.value)
        if record is None:
            return None
        return self._to_domain(record)

    def save(self, index: PortfolioRetrievalIndex) -> None:
        record = self._session.get(EngineeringPortfolioRetrievalIndexRecord, index.index_id.value)
        if record is not None:
            self._enforce_completed_immutability(record, index)

        if record is None:
            self._session.add(PortfolioRetrievalIndexMapper.to_record(index))
        else:
            PortfolioRetrievalIndexMapper.apply_to_record(index, record)

        index_id = index.index_id.value
        self._session.execute(
            delete(EngineeringPortfolioRetrievalChunkRecord).where(
                EngineeringPortfolioRetrievalChunkRecord.index_id == index_id
            )
        )
        self._session.execute(
            delete(EngineeringPortfolioRetrievalDocumentRecord).where(
                EngineeringPortfolioRetrievalDocumentRecord.index_id == index_id
            )
        )
        for document in index.documents:
            self._session.add(PortfolioRetrievalIndexMapper.to_document_record(document))
        self._session.flush()
        for chunk in index.chunks:
            self._session.add(PortfolioRetrievalIndexMapper.to_chunk_record(chunk))
        self._session.flush()
        self._sync_embedding_vectors(index)
        self._session.flush()

    def _enforce_completed_immutability(
        self,
        record: EngineeringPortfolioRetrievalIndexRecord,
        index: PortfolioRetrievalIndex,
    ) -> None:
        if record.status != PortfolioRetrievalIndexStatus.COMPLETED.value:
            return
        if index.status not in _COMPLETED_ALLOWED_TRANSITIONS:
            raise RuntimeError("Completed portfolio retrieval indexes are immutable")
        if index.status is PortfolioRetrievalIndexStatus.COMPLETED:
            existing_document_count = (
                self._session.scalar(
                    select(func.count())
                    .select_from(EngineeringPortfolioRetrievalDocumentRecord)
                    .where(EngineeringPortfolioRetrievalDocumentRecord.index_id == record.id)
                )
                or 0
            )
            existing_chunk_count = (
                self._session.scalar(
                    select(func.count())
                    .select_from(EngineeringPortfolioRetrievalChunkRecord)
                    .where(EngineeringPortfolioRetrievalChunkRecord.index_id == record.id)
                )
                or 0
            )
            if (
                existing_document_count != len(index.documents)
                or existing_chunk_count != len(index.chunks)
                or record.projection_key != index.projection_key.value
            ):
                raise RuntimeError(
                    "Completed portfolio retrieval index inventories are immutable; "
                    "only SUPERSEDED/ARCHIVED status transitions are allowed"
                )

    def _sync_embedding_vectors(self, index: PortfolioRetrievalIndex) -> None:
        """Best-effort sync into optional pgvector column when present."""

        try:
            has_column = self._session.execute(
                text(
                    """
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'engineering_portfolio_retrieval_chunks'
                      AND column_name = 'embedding_vector'
                    """
                )
            ).first()
        except Exception:  # noqa: BLE001
            return
        if has_column is None:
            return
        for chunk in index.chunks:
            if chunk.embedding is None:
                continue
            self._session.execute(
                text(
                    """
                    UPDATE engineering_portfolio_retrieval_chunks
                    SET embedding_vector = CAST(:embedding AS vector)
                    WHERE id = :chunk_id
                    """
                ),
                {
                    "chunk_id": chunk.chunk_id.value,
                    "embedding": "[" + ",".join(str(v) for v in chunk.embedding.values) + "]",
                },
            )

    def find_by_projection_key(
        self,
        projection_key: str,
    ) -> PortfolioRetrievalIndex | None:
        record = self._session.scalars(
            select(EngineeringPortfolioRetrievalIndexRecord).where(
                EngineeringPortfolioRetrievalIndexRecord.projection_key == projection_key.strip()
            )
        ).first()
        if record is None:
            return None
        return self._to_domain(record)

    def list_by_portfolio(
        self,
        portfolio_id: PortfolioId,
    ) -> tuple[PortfolioRetrievalIndex, ...]:
        records = self._session.scalars(
            select(EngineeringPortfolioRetrievalIndexRecord)
            .where(EngineeringPortfolioRetrievalIndexRecord.portfolio_id == portfolio_id.value)
            .order_by(EngineeringPortfolioRetrievalIndexRecord.index_version.asc())
        ).all()
        return tuple(self._to_domain(item) for item in records)

    def get_latest_completed(
        self,
        portfolio_id: PortfolioId,
    ) -> PortfolioRetrievalIndex | None:
        record = self._session.scalars(
            select(EngineeringPortfolioRetrievalIndexRecord)
            .where(
                EngineeringPortfolioRetrievalIndexRecord.portfolio_id == portfolio_id.value,
                EngineeringPortfolioRetrievalIndexRecord.status
                == PortfolioRetrievalIndexStatus.COMPLETED.value,
            )
            .order_by(EngineeringPortfolioRetrievalIndexRecord.index_version.desc())
            .limit(1)
        ).first()
        if record is None:
            return None
        return self._to_domain(record)

    def latest_index_version_for_portfolio(self, portfolio_id: PortfolioId) -> int:
        value = self._session.scalar(
            select(func.max(EngineeringPortfolioRetrievalIndexRecord.index_version)).where(
                EngineeringPortfolioRetrievalIndexRecord.portfolio_id == portfolio_id.value
            )
        )
        return int(value or 0)

    def list_documents_by_index(
        self,
        index_id: PortfolioRetrievalIndexId,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[PortfolioRetrievalDocument, ...]:
        index = self.get(index_id)
        if index is None:
            return ()
        return index.documents[offset : offset + limit]

    def get_document(
        self,
        index_id: PortfolioRetrievalIndexId,
        document_id: PortfolioRetrievalDocumentId,
    ) -> PortfolioRetrievalDocument | None:
        index = self.get(index_id)
        if index is None:
            return None
        for item in index.documents:
            if item.document_id == document_id:
                return item
        return None

    def get_chunk(
        self,
        index_id: PortfolioRetrievalIndexId,
        chunk_id: PortfolioRetrievalChunkId,
    ) -> PortfolioRetrievalChunk | None:
        index = self.get(index_id)
        if index is None:
            return None
        for item in index.chunks:
            if item.chunk_id == chunk_id:
                return item
        return None

    def search(
        self,
        index_id: PortfolioRetrievalIndexId,
        query: PortfolioRetrievalQuery,
        *,
        scope: PortfolioRetrievalScope,
        criticality_lookup: dict[str, RepositoryCriticality] | None = None,
    ) -> PortfolioRetrievalSearchResult:
        index = self.get(index_id)
        if index is None or index.status is not PortfolioRetrievalIndexStatus.COMPLETED:
            return PortfolioRetrievalSearchResult(hits=(), mode=query.mode.value, top_k=query.top_k)
        query_embedding = None
        if (
            query.mode in {RetrievalMode.VECTOR, RetrievalMode.HYBRID}
            and self._embeddings is not None
        ):
            query_embedding = self._embeddings.embed_text(query.query_text)
        return search_portfolio_index(
            index,
            query,
            scope=scope,
            query_embedding=query_embedding,
            criticality_lookup=criticality_lookup,
        )

    def statistics(self, index_id: PortfolioRetrievalIndexId) -> dict[str, int]:
        index = self.get(index_id)
        if index is None:
            return {}
        return {
            "document_count": len(index.documents),
            "chunk_count": len(index.chunks),
            "embedded_chunk_count": sum(1 for item in index.chunks if item.embedding is not None),
        }

    def _to_domain(
        self,
        record: EngineeringPortfolioRetrievalIndexRecord,
    ) -> PortfolioRetrievalIndex:
        documents = list(
            self._session.scalars(
                select(EngineeringPortfolioRetrievalDocumentRecord).where(
                    EngineeringPortfolioRetrievalDocumentRecord.index_id == record.id
                )
            ).all()
        )
        chunks = list(
            self._session.scalars(
                select(EngineeringPortfolioRetrievalChunkRecord).where(
                    EngineeringPortfolioRetrievalChunkRecord.index_id == record.id
                )
            ).all()
        )
        return PortfolioRetrievalIndexMapper.to_domain(record, documents, chunks)
