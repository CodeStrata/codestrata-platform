"""Memory vs pgvector parity for grounded answering (Phase 5.6)."""

from __future__ import annotations

import os

import pytest

from codestrata.config.settings import (
    KnowledgeAnsweringSettings,
    KnowledgeEmbeddingSettings,
    KnowledgeRetrievalSettings,
)
from codestrata_platform.rag.application.answering import (
    DeterministicExtractiveAnswerProvider,
    GroundedAnswerEngine,
)
from codestrata_platform.rag.application.retrieval import RepositoryRetriever
from codestrata_platform.rag.domain import (
    AnswerStatus,
    GroundedAnswerRequest,
    RetrievalScope,
    VectorRecord,
)
from codestrata_platform.rag.embedding import DeterministicEmbeddingProvider
from codestrata_platform.rag.vector_store import InMemoryVectorStore
from codestrata_platform.rag.vector_store.pgvector import PgVectorStore

PG_URL = (
    os.environ.get("CODESTRATA_DATABASE_URL", "").strip()
    or os.environ.get("CODESTRATA_PGVECTOR_URL", "").strip()
)


def _records(provider: DeterministicEmbeddingProvider) -> list[VectorRecord]:
    texts = [
        (
            "arch",
            "repository architecture overview layered modules",
            {"source_type": "architecture"},
        ),
        (
            "sec",
            "high severity security finding in auth",
            {"source_type": "security", "severity": "high", "finding_id": "f-1"},
        ),
        (
            "dep",
            "dependency modernization risk for jackson",
            {"source_type": "dependency"},
        ),
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


def _engine(store, provider: DeterministicEmbeddingProvider) -> GroundedAnswerEngine:
    retriever = RepositoryRetriever(
        embedding_provider=provider,
        vector_store=store,
        retrieval_settings=KnowledgeRetrievalSettings(enabled=True),
        embedding_settings=KnowledgeEmbeddingSettings(
            enabled=True, provider="deterministic", dimension=16
        ),
    )
    return GroundedAnswerEngine(
        retriever=retriever,
        answer_provider=DeterministicExtractiveAnswerProvider(),
        answering_settings=KnowledgeAnsweringSettings(enabled=True),
        retrieval_settings=KnowledgeRetrievalSettings(enabled=True),
    )


@pytest.mark.skipif(not PG_URL, reason="CODESTRATA_DATABASE_URL / CODESTRATA_PGVECTOR_URL not set")
def test_memory_pgvector_answer_parity() -> None:
    provider = DeterministicEmbeddingProvider(dimension=16)
    records = _records(provider)

    memory = InMemoryVectorStore()
    memory.upsert(records)

    try:
        pg_cm = PgVectorStore(
            connection_string=PG_URL,
            schema="codestrata_answer_parity",
            dimension=16,
            hnsw=True,
        )
        pg = pg_cm.__enter__()
    except Exception as error:  # noqa: BLE001 - optional integration
        pytest.skip(f"PostgreSQL + pgvector unavailable: {error}")

    try:
        with pg._connection.cursor() as cur:  # noqa: SLF001
            cur.execute('DELETE FROM "codestrata_answer_parity".knowledge_vectors')
        pg._connection.commit()  # noqa: SLF001
        pg.upsert(records)

        request = GroundedAnswerRequest(
            question="How is the repository architecture organized?",
            scope=RetrievalScope(
                tenant_id="parity",
                repository_id="repo-parity",
                scan_id="scan-parity",
            ),
            top_k=5,
        )
        mem_result = _engine(memory, provider).answer(request)
        pg_result = _engine(pg, provider).answer(request)

        assert mem_result.status in {AnswerStatus.SUCCESS, AnswerStatus.PARTIAL}
        assert pg_result.status in {AnswerStatus.SUCCESS, AnswerStatus.PARTIAL}
        assert mem_result.answer is not None and pg_result.answer is not None
        mem_labels = [c.citation_label for c in mem_result.answer.citations]
        pg_labels = [c.citation_label for c in pg_result.answer.citations]
        assert mem_labels == pg_labels
        assert [s.text for s in mem_result.answer.statements] == [
            s.text for s in pg_result.answer.statements
        ]
    finally:
        pg_cm.__exit__(None, None, None)
