"""Provider parity: InMemoryVectorStore vs PgVectorStore retrieval."""

from __future__ import annotations

import os

import pytest

from aimf.application.knowledge.retrieval import RepositoryRetriever
from aimf.config.settings import KnowledgeEmbeddingSettings, KnowledgeRetrievalSettings
from aimf.domain.knowledge import (
    RetrievalFilters,
    RetrievalRequest,
    RetrievalScope,
    VectorRecord,
)
from aimf.infrastructure.embedding import DeterministicEmbeddingProvider
from aimf.infrastructure.vector_store import InMemoryVectorStore
from aimf.infrastructure.vector_store.pgvector import PgVectorStore

PG_URL = (
    os.environ.get("CODESTRATA_DATABASE_URL", "").strip()
    or os.environ.get("AIMF_PGVECTOR_URL", "").strip()
)


def _records(provider: DeterministicEmbeddingProvider) -> list[VectorRecord]:
    texts = [
        ("arch", "repository architecture overview", {"source_type": "architecture"}),
        ("sec", "high severity security finding", {"source_type": "security", "severity": "high"}),
        ("dep", "dependency modernization risk", {"source_type": "dependency"}),
    ]
    out: list[VectorRecord] = []
    for entity_id, text, extra in texts:
        emb = list(provider.embed_text(text).embedding)
        out.append(
            VectorRecord.create(
                entity_id=entity_id,
                embedding=emb,
                text=text,
                metadata={
                    "tenant_id": "parity",
                    "repository_id": "repo-parity",
                    "scan_id": "scan-parity",
                    "document_id": f"kd:{entity_id}",
                    "chunk_id": f"kc:{entity_id}",
                    "chunk_sequence": 0,
                    "content_hash": f"hash-{entity_id}",
                    **extra,
                },
            )
        )
    return out


def _run(store, provider: DeterministicEmbeddingProvider, query: str, **filters):
    retriever = RepositoryRetriever(
        embedding_provider=provider,
        vector_store=store,
        retrieval_settings=KnowledgeRetrievalSettings(enabled=True),
        embedding_settings=KnowledgeEmbeddingSettings(
            enabled=True, provider="deterministic", dimension=16
        ),
    )
    return retriever.retrieve(
        RetrievalRequest(
            query=query,
            scope=RetrievalScope(
                tenant_id="parity",
                repository_id="repo-parity",
                scan_id="scan-parity",
            ),
            filters=RetrievalFilters(**filters) if filters else RetrievalFilters(),
            top_k=5,
            candidate_limit=10,
        )
    )


@pytest.mark.skipif(not PG_URL, reason="CODESTRATA_DATABASE_URL / AIMF_PGVECTOR_URL not set")
def test_memory_pgvector_retrieval_parity() -> None:
    provider = DeterministicEmbeddingProvider(dimension=16)
    records = _records(provider)

    memory = InMemoryVectorStore()
    memory.upsert(records)

    with PgVectorStore(
        connection_string=PG_URL,
        schema="codestrata_retrieval_parity",
        dimension=16,
        hnsw=True,
    ) as pg:
        # clear schema vectors for isolation
        with pg._connection.cursor() as cur:  # noqa: SLF001
            cur.execute('DELETE FROM "codestrata_retrieval_parity".knowledge_vectors')
        pg._connection.commit()  # noqa: SLF001
        pg.upsert(records)

        mem_result = _run(memory, provider, "architecture overview")
        pg_result = _run(pg, provider, "architecture overview")
        assert [h.record_id for h in mem_result.context.hits] == [
            h.record_id for h in pg_result.context.hits
        ]
        for left, right in zip(mem_result.context.hits, pg_result.context.hits, strict=True):
            assert abs(left.score - right.score) < 1e-5

        mem_f = _run(memory, provider, "security finding", source_types=("security",))
        pg_f = _run(pg, provider, "security finding", source_types=("security",))
        assert [h.record_id for h in mem_f.context.hits] == [
            h.record_id for h in pg_f.context.hits
        ]
