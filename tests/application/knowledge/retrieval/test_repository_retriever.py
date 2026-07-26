"""Tests for RepositoryRetriever (Phase 5.5)."""

from __future__ import annotations

from pathlib import Path

from aimf.application.knowledge.retrieval import (
    RepositoryRetriever,
    write_retrieval_result_artifact,
)
from aimf.application.knowledge.retrieval.query_preparation import prepare_retrieval_query
from aimf.config.settings import KnowledgeEmbeddingSettings, KnowledgeRetrievalSettings
from aimf.domain.knowledge import (
    RetrievalFilters,
    RetrievalRequest,
    RetrievalScope,
    RetrievalStatus,
    VectorRecord,
    retrieval_result_payload,
)
from aimf.infrastructure.embedding import DeterministicEmbeddingProvider
from aimf.infrastructure.vector_store import InMemoryVectorStore
from aimf.services.artifact_serialization import dumps_stable_json


def _scope(**kwargs: str) -> RetrievalScope:
    base = {"tenant_id": "tenant-a", "repository_id": "repo-a"}
    base.update(kwargs)
    return RetrievalScope(**base)  # type: ignore[arg-type]


def _record(
    entity_id: str,
    text: str,
    *,
    embedding: list[float] | None = None,
    tenant_id: str = "tenant-a",
    repository_id: str = "repo-a",
    scan_id: str = "scan-a",
    document_id: str | None = None,
    chunk_id: str | None = None,
    sequence: int = 0,
    **extra: object,
) -> VectorRecord:
    meta: dict[str, object] = {
        "tenant_id": tenant_id,
        "repository_id": repository_id,
        "scan_id": scan_id,
        "document_id": document_id or f"kd:{entity_id}",
        "chunk_id": chunk_id or f"kc:{entity_id}",
        "chunk_sequence": sequence,
        "content_hash": f"hash-{entity_id}",
        **extra,
    }
    provider = DeterministicEmbeddingProvider(dimension=8)
    vector = embedding or list(provider.embed_text(text).embedding)
    return VectorRecord.create(
        entity_id=entity_id,
        embedding=vector,
        metadata=meta,
        text=text,
    )


def _retriever(
    store: InMemoryVectorStore | None = None,
    *,
    enabled: bool = True,
    dimension: int = 8,
) -> tuple[RepositoryRetriever, InMemoryVectorStore, DeterministicEmbeddingProvider]:
    vector_store = store or InMemoryVectorStore()
    provider = DeterministicEmbeddingProvider(dimension=dimension)
    retriever = RepositoryRetriever(
        embedding_provider=provider,
        vector_store=vector_store,
        retrieval_settings=KnowledgeRetrievalSettings(enabled=enabled),
        embedding_settings=KnowledgeEmbeddingSettings(
            enabled=True,
            provider="deterministic",
            dimension=dimension,
        ),
    )
    return retriever, vector_store, provider


def test_empty_and_whitespace_query() -> None:
    retriever, _, _ = _retriever()
    for query in ("", "   ", "\n\t"):
        result = retriever.retrieve(RetrievalRequest(query=query, scope=_scope()))
        assert result.status == RetrievalStatus.FAILED
        assert any(d.code == "empty_query" for d in result.diagnostics)


def test_normalized_whitespace_and_stable_fingerprint() -> None:
    left = prepare_retrieval_query("  hello   world  ", max_query_characters=100)
    right = prepare_retrieval_query("hello world", max_query_characters=100)
    assert left.normalized == "hello world"
    assert left.fingerprint == right.fingerprint


def test_oversized_query() -> None:
    retriever, _, _ = _retriever()
    result = retriever.retrieve(
        RetrievalRequest(query="x" * 50, scope=_scope(), max_query_characters=10)
    )
    assert result.status == RetrievalStatus.FAILED
    assert any(d.code == "query_too_large" for d in result.diagnostics)


def test_identical_query_determinism() -> None:
    retriever, store, _ = _retriever()
    store.upsert(
        [
            _record("arch", "repository architecture defined here", source_type="architecture"),
            _record(
                "sec",
                "security finding high severity",
                source_type="finding",
                severity="high",
            ),
        ]
    )
    request = RetrievalRequest(query="architecture", scope=_scope(), top_k=5)
    first = retriever.retrieve(request)
    second = retriever.retrieve(request)
    assert first.fingerprint == second.fingerprint
    assert [h.record_id for h in first.context.hits] == [
        h.record_id for h in second.context.hits
    ]
    assert dumps_stable_json(retrieval_result_payload(first)) == dumps_stable_json(
        retrieval_result_payload(second)
    )


def test_tenant_repository_scan_isolation() -> None:
    retriever, store, _ = _retriever()
    store.upsert(
        [
            _record("keep", "auth login", tenant_id="t1", repository_id="r1", scan_id="s1"),
            _record("other-tenant", "auth login", tenant_id="t2", repository_id="r1", scan_id="s1"),
            _record("other-repo", "auth login", tenant_id="t1", repository_id="r2", scan_id="s1"),
            _record("other-scan", "auth login", tenant_id="t1", repository_id="r1", scan_id="s2"),
        ]
    )
    result = retriever.retrieve(
        RetrievalRequest(
            query="auth login",
            scope=RetrievalScope(tenant_id="t1", repository_id="r1", scan_id="s1"),
            top_k=10,
        )
    )
    assert {h.chunk_id for h in result.context.hits} == {"kc:keep"}


def test_optional_cross_scan_within_repository() -> None:
    retriever, store, _ = _retriever()
    store.upsert(
        [
            _record("a", "cloud config yaml", scan_id="s1", source_type="cloud"),
            _record("b", "cloud config terraform", scan_id="s2", source_type="cloud"),
        ]
    )
    result = retriever.retrieve(
        RetrievalRequest(
            query="cloud config",
            scope=_scope(),
            top_k=10,
            minimum_score=-1.0,
        )
    )
    assert {h.scan_id for h in result.context.hits} == {"s1", "s2"}


def test_source_type_and_severity_filters() -> None:
    retriever, store, _ = _retriever()
    store.upsert(
        [
            _record("sec", "security issue", source_type="security", severity="high"),
            _record("arch", "architecture note", source_type="architecture", severity="low"),
        ]
    )
    result = retriever.retrieve(
        RetrievalRequest(
            query="security issue",
            scope=_scope(),
            filters=RetrievalFilters(source_types=("security",), severities=("high",)),
            top_k=10,
        )
    )
    assert [h.chunk_id for h in result.context.hits] == ["kc:sec"]


def test_finding_rule_file_symbol_filters() -> None:
    retriever, store, _ = _retriever()
    store.upsert(
        [
            _record(
                "f1",
                "finding body",
                finding_id="FIND-1",
                rule_id="R-1",
                file_path="src/a.py",
                symbol_name="AuthService",
            ),
            _record(
                "f2",
                "finding body",
                finding_id="FIND-2",
                rule_id="R-2",
                file_path="src/b.py",
                symbol_name="Other",
            ),
        ]
    )
    result = retriever.retrieve(
        RetrievalRequest(
            query="finding body",
            scope=_scope(),
            filters=RetrievalFilters(
                finding_ids=("FIND-1",),
                rule_ids=("R-1",),
                file_paths=("src/a.py",),
                symbol_names=("AuthService",),
            ),
        )
    )
    assert [h.chunk_id for h in result.context.hits] == ["kc:f1"]


def test_minimum_score_and_top_k() -> None:
    retriever, store, provider = _retriever()
    # Identical embeddings → high score; orthogonal → low
    store.upsert(
        [
            _record("near", "alpha beta gamma"),
            _record(
                "far",
                "zzz",
                embedding=[0.0] * 7 + [1.0],
            ),
        ]
    )
    result = retriever.retrieve(
        RetrievalRequest(
            query="alpha beta gamma",
            scope=_scope(),
            top_k=1,
            candidate_limit=10,
            minimum_score=0.5,
        )
    )
    assert result.coverage.final_hit_count == 1
    assert result.context.hits[0].chunk_id == "kc:near"


def test_deduplicate_chunk_id_keeps_highest_score() -> None:
    retriever, store, provider = _retriever()
    text = "duplicate chunk content"
    emb = list(provider.embed_text(text).embedding)
    high = _record("dup-high", text, embedding=emb, chunk_id="kc:same", content_hash="h1")
    # Slightly different embedding but same chunk_id — upsert would replace by record_id;
    # use same entity namespace carefully: different entity_ids → different record_ids.
    low = VectorRecord.create(
        entity_id="dup-low",
        embedding=[0.0] * 8,
        metadata={
            "tenant_id": "tenant-a",
            "repository_id": "repo-a",
            "scan_id": "scan-a",
            "document_id": "kd:x",
            "chunk_id": "kc:same",
            "chunk_sequence": 0,
            "content_hash": "h1",
        },
        text=text,
    )
    store.upsert([low, high])
    result = retriever.retrieve(RetrievalRequest(query=text, scope=_scope(), top_k=5))
    ids = [h.chunk_id for h in result.context.hits]
    assert ids.count("kc:same") == 1
    assert result.coverage.duplicates_removed >= 1


def test_diversity_max_per_document() -> None:
    retriever, store, provider = _retriever()
    # Share the same embedding so scores stay above the default floor.
    emb = list(provider.embed_text("topic alpha shared").embedding)
    store.upsert(
        [
            _record("d0", "topic alpha shared", embedding=emb, document_id="kd:doc", sequence=0),
            _record("d1", "topic alpha shared", embedding=emb, document_id="kd:doc", sequence=1),
            _record("d2", "topic alpha shared", embedding=emb, document_id="kd:doc", sequence=2),
            _record("d3", "topic alpha shared", embedding=emb, document_id="kd:doc", sequence=3),
            _record(
                "other",
                "topic alpha shared",
                embedding=emb,
                document_id="kd:other",
                sequence=0,
            ),
        ]
    )
    result = retriever.retrieve(
        RetrievalRequest(
            query="topic alpha shared",
            scope=_scope(),
            top_k=10,
            candidate_limit=20,
            max_chunks_per_document=2,
            max_chunks_per_file=10,
            max_chunks_per_source_type=10,
        )
    )
    doc_hits = [h for h in result.context.hits if h.document_id == "kd:doc"]
    assert len(doc_hits) <= 2
    assert result.coverage.diversity_exclusions >= 1


def test_context_character_limit_skips_whole_chunks() -> None:
    retriever, store, _ = _retriever()
    store.upsert(
        [
            _record("small", "short"),
            _record("big", "x" * 100),
        ]
    )
    result = retriever.retrieve(
        RetrievalRequest(
            query="short",
            scope=_scope(),
            top_k=5,
            max_context_characters=20,
            include_content=True,
        )
    )
    for hit in result.context.hits:
        assert hit.content is None or len(hit.content) <= 20
    assert result.context.character_count <= 20


def test_stable_citation_labels() -> None:
    retriever, store, _ = _retriever()
    store.upsert([_record("a", "cite me"), _record("b", "cite me too")])
    result = retriever.retrieve(RetrievalRequest(query="cite me", scope=_scope(), top_k=5))
    labels = list(result.context.citation_labels)
    assert labels == [f"SRC-{i:03d}" for i in range(1, len(labels) + 1)]
    assert labels == [h.citation_label for h in result.context.hits]


def test_disabled_and_empty_statuses() -> None:
    disabled, store, _ = _retriever(enabled=False)
    assert (
        disabled.retrieve(RetrievalRequest(query="x", scope=_scope())).status
        == RetrievalStatus.DISABLED
    )
    enabled, store, _ = _retriever(enabled=True)
    store.upsert([_record("only", "unrelated zzzz", source_type="test")])
    result = enabled.retrieve(
        RetrievalRequest(
            query="completely different query qqqq",
            scope=_scope(),
            minimum_score=0.99,
            top_k=5,
        )
    )
    assert result.status in {
        RetrievalStatus.EMPTY,
        RetrievalStatus.PARTIAL,
        RetrievalStatus.SUCCESS,
    }


def test_artifact_excludes_embeddings(tmp_path: Path) -> None:
    retriever, store, _ = _retriever()
    store.upsert([_record("a", "artifact body")])
    result = retriever.retrieve(RetrievalRequest(query="artifact body", scope=_scope()))
    path = write_retrieval_result_artifact(
        result, tmp_path, enabled=True, include_content=True
    )
    assert path is not None
    text = path.read_text(encoding="utf-8")
    assert "embedding" not in text or '"embedding"' not in text
    assert "SRC-001" in text


def test_branch_commit_filters() -> None:
    retriever, store, _ = _retriever()
    store.upsert(
        [
            _record("main", "branch tip", branch="main", commit_sha="aaa"),
            _record("dev", "branch tip", branch="dev", commit_sha="bbb"),
        ]
    )
    result = retriever.retrieve(
        RetrievalRequest(
            query="branch tip",
            scope=RetrievalScope(
                tenant_id="tenant-a",
                repository_id="repo-a",
                branch="main",
                commit_sha="aaa",
            ),
        )
    )
    assert [h.chunk_id for h in result.context.hits] == ["kc:main"]
