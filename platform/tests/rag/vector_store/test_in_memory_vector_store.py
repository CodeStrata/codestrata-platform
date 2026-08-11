"""Tests for InMemoryVectorStore (Phase 5.1)."""

from __future__ import annotations

import pytest

from codestrata_platform.rag.domain import (
    IndexScope,
    VectorFilter,
    VectorQuery,
    VectorRecord,
)
from codestrata_platform.rag.vector_store import (
    InMemoryVectorStore,
    cosine_similarity,
    create_vector_store,
)


def _record(
    entity_id: str,
    embedding: list[float],
    *,
    tenant_id: str = "tenant-a",
    repository_id: str = "repo-a",
    scan_id: str = "scan-a",
    **extra: object,
) -> VectorRecord:
    metadata = {
        "tenant_id": tenant_id,
        "repository_id": repository_id,
        "scan_id": scan_id,
        **extra,
    }
    return VectorRecord.create(
        entity_id=entity_id,
        embedding=embedding,
        metadata=metadata,
    )


def test_cosine_similarity_ordering() -> None:
    store = InMemoryVectorStore()
    store.upsert(
        [
            _record("a", [1.0, 0.0, 0.0]),
            _record("b", [0.9, 0.1, 0.0]),
            _record("c", [0.0, 1.0, 0.0]),
        ]
    )
    results = store.search(VectorQuery(embedding=(1.0, 0.0, 0.0), top_k=3))
    assert [item.record.entity_id for item in results] == ["a", "b", "c"]
    assert results[0].score > results[1].score > results[2].score


def test_metadata_filtering() -> None:
    store = InMemoryVectorStore()
    store.upsert(
        [
            _record("keep", [1.0, 0.0], language="java"),
            _record("drop", [1.0, 0.0], language="python"),
        ]
    )
    results = store.search(
        VectorQuery(
            embedding=(1.0, 0.0),
            top_k=10,
            filter=VectorFilter(equals={"language": "java"}),
        )
    )
    assert len(results) == 1
    assert results[0].record.entity_id == "keep"


def test_tenant_repository_scan_isolation() -> None:
    store = InMemoryVectorStore()
    store.upsert(
        [
            _record("t1", [1.0, 0.0], tenant_id="t1", repository_id="r1", scan_id="s1"),
            _record("t2", [1.0, 0.0], tenant_id="t2", repository_id="r1", scan_id="s1"),
            _record("r2", [1.0, 0.0], tenant_id="t1", repository_id="r2", scan_id="s1"),
            _record("s2", [1.0, 0.0], tenant_id="t1", repository_id="r1", scan_id="s2"),
        ]
    )
    tenant_hits = store.search(
        VectorQuery(
            embedding=(1.0, 0.0),
            top_k=10,
            filter=VectorFilter(tenant_id="t1"),
        )
    )
    assert {item.record.entity_id for item in tenant_hits} == {"t1", "r2", "s2"}

    repo_hits = store.search(
        VectorQuery(
            embedding=(1.0, 0.0),
            top_k=10,
            filter=VectorFilter(tenant_id="t1", repository_id="r1"),
        )
    )
    assert {item.record.entity_id for item in repo_hits} == {"t1", "s2"}

    scan_hits = store.search(
        VectorQuery(
            embedding=(1.0, 0.0),
            top_k=10,
            filter=VectorFilter(tenant_id="t1", repository_id="r1", scan_id="s1"),
        )
    )
    assert [item.record.entity_id for item in scan_hits] == ["t1"]


def test_deterministic_search_results() -> None:
    store = InMemoryVectorStore()
    # Equal scores: stable tie-break by record_id.
    store.upsert(
        [
            _record("z-entity", [1.0, 0.0]),
            _record("a-entity", [1.0, 0.0]),
            _record("m-entity", [1.0, 0.0]),
        ]
    )
    left = store.search(VectorQuery(embedding=(1.0, 0.0), top_k=10))
    right = store.search(VectorQuery(embedding=(1.0, 0.0), top_k=10))
    assert [item.record_id for item in left] == [item.record_id for item in right]
    assert [item.record_id for item in left] == sorted(item.record_id for item in left)


def test_empty_vector_store() -> None:
    store = InMemoryVectorStore()
    assert len(store) == 0
    assert store.search(VectorQuery(embedding=(1.0, 0.0), top_k=5)) == ()
    assert store.health().healthy is True
    assert store.capabilities().provider_id == "memory"


def test_duplicate_upserts_replace() -> None:
    store = InMemoryVectorStore()
    first = _record("same", [1.0, 0.0], language="java")
    second = _record("same", [0.0, 1.0], language="python")
    assert first.record_id == second.record_id
    store.upsert([first])
    store.upsert([second])
    assert len(store) == 1
    results = store.search(VectorQuery(embedding=(0.0, 1.0), top_k=1))
    assert results[0].record.metadata["language"] == "python"


def test_scoped_deletion() -> None:
    store = InMemoryVectorStore()
    store.upsert(
        [
            _record("keep", [1.0, 0.0], tenant_id="t1", repository_id="r1", scan_id="s1"),
            _record("drop", [1.0, 0.0], tenant_id="t1", repository_id="r1", scan_id="s2"),
            _record("other", [1.0, 0.0], tenant_id="t2", repository_id="r1", scan_id="s2"),
        ]
    )
    deleted = store.delete_scope(IndexScope(tenant_id="t1", repository_id="r1", scan_id="s2"))
    assert deleted == 1
    remaining = store.search(VectorQuery(embedding=(1.0, 0.0), top_k=10))
    assert {item.record.entity_id for item in remaining} == {"keep", "other"}


def test_cosine_similarity_zero_vector() -> None:
    assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0
    with pytest.raises(ValueError, match="dimensions"):
        cosine_similarity([1.0], [1.0, 0.0])


def test_create_vector_store_memory_default() -> None:
    store = create_vector_store()
    assert store.capabilities().provider_id == "memory"
