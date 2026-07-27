"""SqlAlchemy Engineering Retrieval Index repository."""

from __future__ import annotations

from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.retrieval.embedding import EmbeddingProvider
from codestrata_platform.domain.retrieval.identifiers import RetrievalIndexId
from codestrata_platform.domain.retrieval.index import EngineeringRetrievalIndex
from codestrata_platform.domain.retrieval.lifecycle import RetrievalIndexStatus
from codestrata_platform.domain.retrieval.query import RetrievalQuery, RetrievalScope
from codestrata_platform.domain.retrieval.result import RetrievalSearchResult
from codestrata_platform.domain.retrieval.taxonomy import RetrievalMode
from codestrata_platform.infrastructure.persistence.mappers.retrieval_mapper import (
    RetrievalIndexMapper,
)
from codestrata_platform.infrastructure.persistence.models.retrieval_records import (
    EngineeringRetrievalChunkRecord,
    EngineeringRetrievalDocumentRecord,
    EngineeringRetrievalIndexRecord,
)
from codestrata_platform.infrastructure.retrieval.search import search_index


class SqlAlchemyRetrievalIndexRepository:
    """Durable RetrievalIndexRepository + RetrievalQueryRepository adapter."""

    def __init__(
        self,
        session: Session,
        *,
        embeddings: EmbeddingProvider | None = None,
    ) -> None:
        self._session = session
        self._embeddings = embeddings

    def get(self, index_id: RetrievalIndexId) -> EngineeringRetrievalIndex | None:
        record = self._session.get(EngineeringRetrievalIndexRecord, index_id.value)
        if record is None:
            return None
        return self._to_domain(record)

    def save(self, index: EngineeringRetrievalIndex) -> None:
        record = self._session.get(EngineeringRetrievalIndexRecord, index.index_id.value)
        if record is None:
            self._session.add(RetrievalIndexMapper.to_record(index))
        else:
            RetrievalIndexMapper.apply_to_record(index, record)

        index_id = index.index_id.value
        self._session.execute(
            delete(EngineeringRetrievalChunkRecord).where(
                EngineeringRetrievalChunkRecord.index_id == index_id
            )
        )
        self._session.execute(
            delete(EngineeringRetrievalDocumentRecord).where(
                EngineeringRetrievalDocumentRecord.index_id == index_id
            )
        )
        for document in index.documents:
            self._session.add(RetrievalIndexMapper.to_document_record(document))
        self._session.flush()
        for chunk in index.chunks:
            record = RetrievalIndexMapper.to_chunk_record(chunk)
            self._session.add(record)
        self._session.flush()
        self._sync_embedding_vectors(index)
        self._session.flush()

    def _sync_embedding_vectors(self, index: EngineeringRetrievalIndex) -> None:
        """Best-effort sync into optional pgvector column when present."""

        try:
            has_column = self._session.execute(
                text(
                    """
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'engineering_retrieval_chunks'
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
                    UPDATE engineering_retrieval_chunks
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
    ) -> EngineeringRetrievalIndex | None:
        record = self._session.scalars(
            select(EngineeringRetrievalIndexRecord).where(
                EngineeringRetrievalIndexRecord.projection_key == projection_key.strip()
            )
        ).first()
        if record is None:
            return None
        return self._to_domain(record)

    def list_by_repository(
        self,
        repository_id: RepositoryId,
    ) -> tuple[EngineeringRetrievalIndex, ...]:
        records = self._session.scalars(
            select(EngineeringRetrievalIndexRecord)
            .where(EngineeringRetrievalIndexRecord.repository_id == repository_id.value)
            .order_by(EngineeringRetrievalIndexRecord.index_version.asc())
        ).all()
        return tuple(self._to_domain(item) for item in records)

    def get_latest_completed(
        self,
        repository_id: RepositoryId,
    ) -> EngineeringRetrievalIndex | None:
        record = self._session.scalars(
            select(EngineeringRetrievalIndexRecord)
            .where(
                EngineeringRetrievalIndexRecord.repository_id == repository_id.value,
                EngineeringRetrievalIndexRecord.status == RetrievalIndexStatus.COMPLETED.value,
            )
            .order_by(EngineeringRetrievalIndexRecord.index_version.desc())
            .limit(1)
        ).first()
        if record is None:
            return None
        return self._to_domain(record)

    def latest_index_version_for_repository(self, repository_id: RepositoryId) -> int:
        value = self._session.scalar(
            select(func.max(EngineeringRetrievalIndexRecord.index_version)).where(
                EngineeringRetrievalIndexRecord.repository_id == repository_id.value
            )
        )
        return int(value or 0)

    def search(
        self,
        index_id: RetrievalIndexId,
        query: RetrievalQuery,
        *,
        scope: RetrievalScope,
    ) -> RetrievalSearchResult:
        index = self.get(index_id)
        if index is None or index.status is not RetrievalIndexStatus.COMPLETED:
            return RetrievalSearchResult(hits=(), mode=query.mode.value, top_k=query.top_k)
        query_embedding = None
        if (
            query.mode in {RetrievalMode.VECTOR, RetrievalMode.HYBRID}
            and self._embeddings is not None
        ):
            query_embedding = self._embeddings.embed_text(query.query_text)
        return search_index(index, query, scope=scope, query_embedding=query_embedding)

    def statistics(self, index_id: RetrievalIndexId) -> dict[str, int]:
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
        record: EngineeringRetrievalIndexRecord,
    ) -> EngineeringRetrievalIndex:
        documents = list(
            self._session.scalars(
                select(EngineeringRetrievalDocumentRecord).where(
                    EngineeringRetrievalDocumentRecord.index_id == record.id
                )
            ).all()
        )
        chunks = list(
            self._session.scalars(
                select(EngineeringRetrievalChunkRecord).where(
                    EngineeringRetrievalChunkRecord.index_id == record.id
                )
            ).all()
        )
        return RetrievalIndexMapper.to_domain(record, documents, chunks)
