"""Tests for PgVectorStore (Phase 5.4).

Integration tests require PostgreSQL + pgvector. Set ``CODESTRATA_PGVECTOR_URL``
(or pass ``connection_string``) to run them; otherwise they skip.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

from codestrata.config.settings import load_settings
from codestrata_platform.rag.domain import (
    IndexScope,
    VectorFilter,
    VectorQuery,
    VectorRecord,
)
from codestrata_platform.rag.embedding import DeterministicEmbeddingProvider
from codestrata_platform.rag.vector_store import InMemoryVectorStore, create_vector_store
from codestrata_platform.rag.vector_store.pgvector import PgVectorStore
from codestrata_platform.rag.vector_store.pgvector.schema import build_schema_statements

PG_URL = (
    os.environ.get("CODESTRATA_DATABASE_URL", "").strip()
    or os.environ.get("CODESTRATA_PGVECTOR_URL", "").strip()
)


def _record(
    entity_id: str,
    embedding: list[float],
    *,
    tenant_id: str = "tenant-a",
    repository_id: str = "repo-a",
    scan_id: str = "scan-a",
    document_id: str | None = None,
    chunk_id: str | None = None,
    **extra: object,
) -> VectorRecord:
    metadata: dict[str, object] = {
        "tenant_id": tenant_id,
        "repository_id": repository_id,
        "scan_id": scan_id,
        **extra,
    }
    if document_id is not None:
        metadata["document_id"] = document_id
    if chunk_id is not None:
        metadata["chunk_id"] = chunk_id
    return VectorRecord.create(
        entity_id=entity_id,
        embedding=embedding,
        metadata=metadata,
    )


@pytest.fixture
def store() -> Iterator[PgVectorStore]:
    if not PG_URL:
        pytest.skip("CODESTRATA_PGVECTOR_URL not set (PostgreSQL + pgvector required)")
    schema = "codestrata_test_phase_54"
    dimension = 4
    try:
        pg_cm = PgVectorStore(
            connection_string=PG_URL,
            schema=schema,
            dimension=dimension,
            hnsw=True,
            migrate=True,
        )
        pg = pg_cm.__enter__()
    except Exception as error:  # noqa: BLE001 - optional integration
        pytest.skip(f"PostgreSQL + pgvector unavailable: {error}")
    try:
        # Isolate each test by clearing vectors (and dependent stubs).
        with pg._connection.cursor() as cur:  # noqa: SLF001 - test cleanup
            cur.execute(f'DELETE FROM "{schema}".knowledge_vectors')
            cur.execute(f'DELETE FROM "{schema}".knowledge_chunks')
            cur.execute(f'DELETE FROM "{schema}".knowledge_documents')
        pg._connection.commit()  # noqa: SLF001
        yield pg
    finally:
        pg_cm.__exit__(None, None, None)


def test_schema_statements_are_deterministic() -> None:
    left = build_schema_statements(schema="codestrata", dimension=384, hnsw=True)
    right = build_schema_statements(schema="codestrata", dimension=384, hnsw=True)
    assert left == right
    joined = "\n".join(left)
    assert "knowledge_documents" in joined
    assert "knowledge_chunks" in joined
    assert "knowledge_vectors" in joined
    assert "vector(384)" in joined
    assert "hnsw" in joined.lower()
    assert "vector_cosine_ops" in joined


def test_insert_and_cosine_search(store: PgVectorStore) -> None:
    store.upsert(
        [
            _record("a", [1.0, 0.0, 0.0, 0.0], document_id="kd:a", chunk_id="kc:a"),
            _record("b", [0.9, 0.1, 0.0, 0.0], document_id="kd:b", chunk_id="kc:b"),
            _record("c", [0.0, 1.0, 0.0, 0.0], document_id="kd:c", chunk_id="kc:c"),
        ]
    )
    results = store.search(VectorQuery(embedding=(1.0, 0.0, 0.0, 0.0), top_k=3))
    assert [item.record.entity_id for item in results] == ["a", "b", "c"]
    assert results[0].score > results[1].score > results[2].score
    assert len(store) == 3


def test_update_replaces_by_record_id(store: PgVectorStore) -> None:
    first = _record("same", [1.0, 0.0, 0.0, 0.0], language="java")
    second = _record("same", [0.0, 1.0, 0.0, 0.0], language="python")
    assert first.record_id == second.record_id
    store.upsert([first])
    store.upsert([second])
    assert len(store) == 1
    results = store.search(VectorQuery(embedding=(0.0, 1.0, 0.0, 0.0), top_k=1))
    assert results[0].record.metadata["language"] == "python"


def test_metadata_filtering(store: PgVectorStore) -> None:
    store.upsert(
        [
            _record("keep", [1.0, 0.0, 0.0, 0.0], language="java"),
            _record("drop", [1.0, 0.0, 0.0, 0.0], language="python"),
        ]
    )
    results = store.search(
        VectorQuery(
            embedding=(1.0, 0.0, 0.0, 0.0),
            top_k=10,
            filter=VectorFilter(equals={"language": "java"}),
        )
    )
    assert len(results) == 1
    assert results[0].record.entity_id == "keep"


def test_tenant_repository_scan_isolation(store: PgVectorStore) -> None:
    store.upsert(
        [
            _record("t1", [1.0, 0.0, 0.0, 0.0], tenant_id="t1", repository_id="r1", scan_id="s1"),
            _record("t2", [1.0, 0.0, 0.0, 0.0], tenant_id="t2", repository_id="r1", scan_id="s1"),
            _record("r2", [1.0, 0.0, 0.0, 0.0], tenant_id="t1", repository_id="r2", scan_id="s1"),
            _record("s2", [1.0, 0.0, 0.0, 0.0], tenant_id="t1", repository_id="r1", scan_id="s2"),
        ]
    )
    tenant_hits = store.search(
        VectorQuery(
            embedding=(1.0, 0.0, 0.0, 0.0),
            top_k=10,
            filter=VectorFilter(tenant_id="t1"),
        )
    )
    assert {item.record.entity_id for item in tenant_hits} == {"t1", "r2", "s2"}

    repo_hits = store.search(
        VectorQuery(
            embedding=(1.0, 0.0, 0.0, 0.0),
            top_k=10,
            filter=VectorFilter(tenant_id="t1", repository_id="r1"),
        )
    )
    assert {item.record.entity_id for item in repo_hits} == {"t1", "s2"}

    scan_hits = store.search(
        VectorQuery(
            embedding=(1.0, 0.0, 0.0, 0.0),
            top_k=10,
            filter=VectorFilter(tenant_id="t1", repository_id="r1", scan_id="s1"),
        )
    )
    assert [item.record.entity_id for item in scan_hits] == ["t1"]


def test_delete_scope(store: PgVectorStore) -> None:
    store.upsert(
        [
            _record("keep", [1.0, 0.0, 0.0, 0.0], tenant_id="t1", repository_id="r1", scan_id="s1"),
            _record("drop", [1.0, 0.0, 0.0, 0.0], tenant_id="t1", repository_id="r1", scan_id="s2"),
            _record(
                "other",
                [1.0, 0.0, 0.0, 0.0],
                tenant_id="t2",
                repository_id="r1",
                scan_id="s2",
            ),
        ]
    )
    deleted = store.delete_scope(IndexScope(tenant_id="t1", repository_id="r1", scan_id="s2"))
    assert deleted == 1
    remaining = store.search(VectorQuery(embedding=(1.0, 0.0, 0.0, 0.0), top_k=10))
    assert {item.record.entity_id for item in remaining} == {"keep", "other"}


def test_delete_ids(store: PgVectorStore) -> None:
    a = _record("a", [1.0, 0.0, 0.0, 0.0])
    b = _record("b", [0.0, 1.0, 0.0, 0.0])
    store.upsert([a, b])
    assert store.delete_ids([a.record_id]) == 1
    assert len(store) == 1


def test_deterministic_ordering_on_score_ties(store: PgVectorStore) -> None:
    store.upsert(
        [
            _record("z-entity", [1.0, 0.0, 0.0, 0.0]),
            _record("a-entity", [1.0, 0.0, 0.0, 0.0]),
            _record("m-entity", [1.0, 0.0, 0.0, 0.0]),
        ]
    )
    left = store.search(VectorQuery(embedding=(1.0, 0.0, 0.0, 0.0), top_k=10))
    right = store.search(VectorQuery(embedding=(1.0, 0.0, 0.0, 0.0), top_k=10))
    assert [item.record_id for item in left] == [item.record_id for item in right]
    assert [item.record_id for item in left] == sorted(item.record_id for item in left)


def test_hnsw_index_created(store: PgVectorStore) -> None:
    health = store.health()
    assert health.healthy is True
    assert health.detail.get("extension_vector") is True
    assert health.detail.get("pgvector_extension") is True
    assert health.detail.get("persistent") is True
    assert health.detail.get("hnsw_index") is True
    dumped = str(health.model_dump())
    assert ":secret@" not in dumped
    assert "password=" not in dumped.lower()
    caps = store.capabilities()
    assert caps.provider_id == "pgvector"
    assert caps.supports_dense is True
    assert caps.supports_hybrid is False


def test_matches_memory_store_search_ordering(store: PgVectorStore) -> None:
    records = [
        _record("a", [1.0, 0.0, 0.0, 0.0]),
        _record("b", [0.8, 0.2, 0.0, 0.0]),
        _record("c", [0.0, 1.0, 0.0, 0.0]),
        _record("d", [0.5, 0.5, 0.0, 0.0]),
    ]
    memory = InMemoryVectorStore()
    memory.upsert(records)
    store.upsert(records)
    query = VectorQuery(embedding=(1.0, 0.0, 0.0, 0.0), top_k=4)
    mem_ids = [item.record_id for item in memory.search(query)]
    pg_ids = [item.record_id for item in store.search(query)]
    assert pg_ids == mem_ids


def test_knowledge_indexer_compatibility(store: PgVectorStore) -> None:
    from codestrata_platform.rag.application.indexing import KnowledgeIndexer, KnowledgeIndexRequest
    from codestrata.config.settings import KnowledgeEmbeddingSettings, KnowledgeIndexingSettings
    from codestrata_platform.rag.domain import (
        KnowledgeChunk,
        KnowledgeCorpus,
        KnowledgeCorpusCoverage,
        KnowledgeDocument,
        KnowledgeMetadata,
        KnowledgeSource,
        KnowledgeSourceType,
        KnowledgeTraceability,
    )

    trace = KnowledgeTraceability(
        source=KnowledgeSource(
            source_type=KnowledgeSourceType.FINDING,
            repository_id="repo-a",
            scan_id="scan-a",
            finding_id="f-1",
            rule_id="R-1",
        ),
        source_id="doc-1",
    )
    doc = KnowledgeDocument.create(
        source_type=KnowledgeSourceType.FINDING,
        source_id="doc-1",
        title="Finding",
        content="document body for pgvector indexer",
        metadata=KnowledgeMetadata(
            tenant_id="tenant-a",
            repository_id="repo-a",
            scan_id="scan-a",
        ),
        traceability=trace,
    )
    chunk = KnowledgeChunk.create(
        document_id=doc.document_id,
        sequence=0,
        content="alpha chunk for pgvector",
        metadata=KnowledgeMetadata(
            tenant_id="tenant-a",
            repository_id="repo-a",
            scan_id="scan-a",
            source_type=KnowledgeSourceType.FINDING,
            finding_id="f-1",
            rule_id="R-1",
        ),
        traceability=trace,
    )
    corpus = KnowledgeCorpus.create(
        documents=(doc,),
        chunks=(chunk,),
        coverage=KnowledgeCorpusCoverage(document_count=1, chunk_count=1),
        metadata=KnowledgeMetadata(
            tenant_id="tenant-a",
            repository_id="repo-a",
            scan_id="scan-a",
        ),
    )
    indexer = KnowledgeIndexer(
        embedding_provider=DeterministicEmbeddingProvider(dimension=4),
        vector_store=store,
        embedding_settings=KnowledgeEmbeddingSettings(
            enabled=True,
            provider="deterministic",
            dimension=4,
        ),
        indexing_settings=KnowledgeIndexingSettings(enabled=True),
    )
    result = indexer.index(
        KnowledgeIndexRequest(
            corpus=corpus,
            scope=IndexScope(tenant_id="tenant-a", repository_id="repo-a", scan_id="scan-a"),
        )
    )
    assert result.manifest.coverage.vector_count == 1
    assert len(store) == 1


def test_create_vector_store_pgvector(tmp_path) -> None:
    if not PG_URL:
        pytest.skip("CODESTRATA_PGVECTOR_URL not set (PostgreSQL + pgvector required)")
    config_file = tmp_path / "codestrata.toml"
    config_file.write_text(
        f"""
        [repository]
        path = "test-fixtures/sample-js-app"

        [knowledge.embedding]
        dimension = 4

        [knowledge.vector_store]
        provider = "pgvector"
        connection_string = "{PG_URL}"
        schema = "codestrata_test_factory"
        hnsw = true
        """,
        encoding="utf-8",
    )
    settings = load_settings(config_file)
    created = create_vector_store(settings.knowledge)
    assert created.capabilities().provider_id == "pgvector"
    if hasattr(created, "close"):
        created.close()  # type: ignore[union-attr]
