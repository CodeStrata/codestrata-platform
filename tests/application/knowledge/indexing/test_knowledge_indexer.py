"""Tests for KnowledgeIndexer (Phase 5.3)."""

from __future__ import annotations

from collections.abc import Sequence

from aimf.application.knowledge.indexing import (
    KnowledgeIndexer,
    KnowledgeIndexRequest,
    write_knowledge_index_artifact,
)
from aimf.config.settings import KnowledgeEmbeddingSettings, KnowledgeIndexingSettings
from aimf.domain.knowledge import (
    IndexScope,
    KnowledgeChunk,
    KnowledgeCorpus,
    KnowledgeCorpusCoverage,
    KnowledgeDocument,
    KnowledgeIndexEntryStatus,
    KnowledgeIndexStatus,
    KnowledgeMetadata,
    KnowledgeSource,
    KnowledgeSourceType,
    KnowledgeTraceability,
    VectorFilter,
    VectorQuery,
)
from aimf.domain.knowledge.embedding import (
    EmbeddingBatchResult,
    EmbeddingDiagnostic,
    EmbeddingModelIdentity,
    EmbeddingProviderCapabilities,
    EmbeddingProviderHealth,
    EmbeddingRequest,
    EmbeddingResult,
    EmbeddingUsage,
)
from aimf.infrastructure.embedding import DeterministicEmbeddingProvider
from aimf.infrastructure.vector_store import InMemoryVectorStore
from aimf.services.artifact_serialization import dumps_stable_json


def _trace(source_id: str = "src") -> KnowledgeTraceability:
    return KnowledgeTraceability(
        source=KnowledgeSource(
            source_type=KnowledgeSourceType.FINDING,
            repository_id="repo-a",
            scan_id="scan-a",
            finding_id="f-1",
            rule_id="R-1",
        ),
        source_id=source_id,
    )


def _chunk(
    *,
    document_id: str,
    sequence: int,
    content: str,
    tenant_id: str = "tenant-a",
    repository_id: str = "repo-a",
    scan_id: str = "scan-a",
) -> KnowledgeChunk:
    return KnowledgeChunk.create(
        document_id=document_id,
        sequence=sequence,
        content=content,
        metadata=KnowledgeMetadata(
            tenant_id=tenant_id,
            repository_id=repository_id,
            scan_id=scan_id,
            source_type=KnowledgeSourceType.FINDING,
            finding_id="f-1",
            rule_id="R-1",
            severity="high",
            confidence="high",
            file_path="src/a.py",
        ),
        traceability=_trace(source_id=f"{document_id}:{sequence}"),
    )


def _corpus(chunks: Sequence[KnowledgeChunk]) -> KnowledgeCorpus:
    docs = [
        KnowledgeDocument.create(
            source_type=KnowledgeSourceType.FINDING,
            source_id="doc-1",
            title="Finding",
            content="document body",
            metadata=KnowledgeMetadata(
                tenant_id="tenant-a",
                repository_id="repo-a",
                scan_id="scan-a",
            ),
            traceability=_trace("doc-1"),
        )
    ]
    return KnowledgeCorpus.create(
        documents=docs,
        chunks=chunks,
        coverage=KnowledgeCorpusCoverage(
            document_count=len(docs),
            chunk_count=len(chunks),
        ),
        metadata=KnowledgeMetadata(
            tenant_id="tenant-a",
            repository_id="repo-a",
            scan_id="scan-a",
        ),
    )


def _indexer(
    store: InMemoryVectorStore | None = None,
    *,
    delete_stale: bool = True,
    batch_size: int = 32,
) -> tuple[KnowledgeIndexer, InMemoryVectorStore]:
    vector_store = store or InMemoryVectorStore()
    indexer = KnowledgeIndexer(
        embedding_provider=DeterministicEmbeddingProvider(dimension=32, batch_size=batch_size),
        vector_store=vector_store,
        embedding_settings=KnowledgeEmbeddingSettings(
            enabled=True,
            provider="deterministic",
            model="deterministic-test-embedding",
            dimension=32,
            batch_size=batch_size,
        ),
        indexing_settings=KnowledgeIndexingSettings(
            enabled=True,
            delete_stale_records=delete_stale,
            write_manifest=False,
        ),
    )
    return indexer, vector_store


def _scope() -> IndexScope:
    return IndexScope(
        tenant_id="tenant-a",
        repository_id="repo-a",
        scan_id="scan-a",
    )


def test_successful_indexing_and_searchability() -> None:
    chunks = (
        _chunk(document_id="kd:1", sequence=0, content="alpha chunk"),
        _chunk(document_id="kd:1", sequence=1, content="beta chunk"),
    )
    indexer, store = _indexer()
    result = indexer.index(
        KnowledgeIndexRequest(corpus=_corpus(chunks), scope=_scope())
    )
    assert result.status == KnowledgeIndexStatus.SUCCESS
    assert result.manifest.coverage.added == 2
    assert result.manifest.coverage.vector_count == 2
    assert len(store) == 2
    record = next(iter(store._records.values()))  # noqa: SLF001 - test inspection
    assert record.metadata["tenant_id"] == "tenant-a"
    assert record.metadata["repository_id"] == "repo-a"
    assert record.metadata["scan_id"] == "scan-a"
    assert record.metadata["finding_id"] == "f-1"
    assert record.metadata["chunk_sequence"] in {0, 1}

    query_vec = DeterministicEmbeddingProvider(dimension=32).embed_text("alpha chunk").embedding
    hits = store.search(
        VectorQuery(
            embedding=query_vec,
            top_k=2,
            filter=VectorFilter(tenant_id="tenant-a", repository_id="repo-a", scan_id="scan-a"),
        )
    )
    assert hits
    assert hits[0].record.metadata["chunk_id"] == chunks[0].chunk_id


def test_empty_corpus_and_disabled() -> None:
    indexer, _store = _indexer()
    empty = indexer.index(KnowledgeIndexRequest(corpus=_corpus(()), scope=_scope()))
    assert empty.status == KnowledgeIndexStatus.EMPTY

    disabled = KnowledgeIndexer(
        embedding_provider=DeterministicEmbeddingProvider(dimension=32),
        vector_store=InMemoryVectorStore(),
        embedding_settings=KnowledgeEmbeddingSettings(enabled=True, dimension=32),
        indexing_settings=KnowledgeIndexingSettings(enabled=False),
    )
    result = disabled.index(KnowledgeIndexRequest(corpus=_corpus((_chunk(
        document_id="kd:1", sequence=0, content="x"
    ),)), scope=_scope()))
    assert result.status == KnowledgeIndexStatus.DISABLED


def test_duplicate_indexing_idempotent_record_ids() -> None:
    chunks = (_chunk(document_id="kd:1", sequence=0, content="same"),)
    indexer, store = _indexer()
    request = KnowledgeIndexRequest(corpus=_corpus(chunks), scope=_scope())
    first = indexer.index(request)
    second = indexer.index(request)
    assert first.manifest.coverage.added == 1
    assert second.manifest.coverage.added == 1
    assert len(store) == 1
    assert first.manifest.entries[0].record_id == second.manifest.entries[0].record_id


def test_unchanged_incremental_indexing() -> None:
    chunks = (
        _chunk(document_id="kd:1", sequence=0, content="keep"),
        _chunk(document_id="kd:1", sequence=1, content="also keep"),
    )
    indexer, store = _indexer()
    first = indexer.index(KnowledgeIndexRequest(corpus=_corpus(chunks), scope=_scope()))
    assert first.manifest.coverage.added == 2
    second = indexer.index(
        KnowledgeIndexRequest(
            corpus=_corpus(chunks),
            scope=_scope(),
            prior_manifest=first.manifest,
        )
    )
    assert second.manifest.coverage.unchanged == 2
    assert second.manifest.coverage.added == 0
    assert second.manifest.coverage.updated == 0
    assert len(store) == 2
    assert second.status == KnowledgeIndexStatus.SUCCESS


def test_added_updated_removed_and_stale_deletion() -> None:
    c0 = _chunk(document_id="kd:1", sequence=0, content="one")
    c1 = _chunk(document_id="kd:1", sequence=1, content="two")
    indexer, store = _indexer(delete_stale=True)
    first = indexer.index(
        KnowledgeIndexRequest(corpus=_corpus((c0, c1)), scope=_scope())
    )
    assert len(store) == 2

    c1_updated = _chunk(document_id="kd:1", sequence=1, content="two-updated")
    c2 = _chunk(document_id="kd:1", sequence=2, content="three")
    second = indexer.index(
        KnowledgeIndexRequest(
            corpus=_corpus((c0, c1_updated, c2)),
            scope=_scope(),
            prior_manifest=first.manifest,
        )
    )
    assert second.manifest.coverage.unchanged == 1
    assert second.manifest.coverage.updated == 1
    assert second.manifest.coverage.added == 1
    assert second.manifest.coverage.removed == 0
    assert len(store) == 3

    third = indexer.index(
        KnowledgeIndexRequest(
            corpus=_corpus((c0, c2)),
            scope=_scope(),
            prior_manifest=second.manifest,
        )
    )
    assert third.manifest.coverage.removed == 1
    assert third.manifest.coverage.stale_deleted == 1
    assert len(store) == 2


def test_stale_deletion_disabled_retains_records() -> None:
    c0 = _chunk(document_id="kd:1", sequence=0, content="one")
    c1 = _chunk(document_id="kd:1", sequence=1, content="two")
    indexer, store = _indexer(delete_stale=False)
    first = indexer.index(KnowledgeIndexRequest(corpus=_corpus((c0, c1)), scope=_scope()))
    second = indexer.index(
        KnowledgeIndexRequest(
            corpus=_corpus((c0,)),
            scope=_scope(),
            prior_manifest=first.manifest,
        )
    )
    assert second.manifest.coverage.removed == 1
    assert second.manifest.coverage.stale_deleted == 0
    assert len(store) == 2
    assert any(d.code == "stale_records_retained" for d in second.diagnostics)


def test_provider_model_incompatibility_forces_reembed() -> None:
    chunks = (_chunk(document_id="kd:1", sequence=0, content="text"),)
    indexer, store = _indexer()
    first = indexer.index(KnowledgeIndexRequest(corpus=_corpus(chunks), scope=_scope()))
    # Build an incompatible prior by rewriting embedding identity via create.
    from aimf.domain.knowledge.embedding import EmbeddingModelIdentity
    from aimf.domain.knowledge.index_manifest import KnowledgeIndexManifest

    incompatible = KnowledgeIndexManifest.create(
        scope=first.manifest.scope,
        embedding_identity=EmbeddingModelIdentity(
            provider_id="deterministic",
            model="other-model",
            model_version="9.9.9",
            dimension=32,
        ),
        entries=first.manifest.entries,
        coverage=first.manifest.coverage,
        corpus_id=first.manifest.corpus_id,
    )
    second = indexer.index(
        KnowledgeIndexRequest(
            corpus=_corpus(chunks),
            scope=_scope(),
            prior_manifest=incompatible,
        )
    )
    assert second.manifest.coverage.added == 1
    assert any(d.code == "prior_manifest_incompatible" for d in second.diagnostics)
    assert len(store) == 1


def test_scope_isolation_skips_foreign_chunks() -> None:
    local = _chunk(document_id="kd:1", sequence=0, content="local")
    foreign = _chunk(
        document_id="kd:2",
        sequence=0,
        content="foreign",
        tenant_id="other-tenant",
        repository_id="repo-a",
        scan_id="scan-a",
    )
    indexer, store = _indexer()
    result = indexer.index(
        KnowledgeIndexRequest(corpus=_corpus((local, foreign)), scope=_scope())
    )
    assert result.manifest.coverage.added == 1
    assert result.manifest.coverage.skipped == 1
    assert len(store) == 1


def test_partial_batch_failure_explicit_status() -> None:
    class FlakyProvider:
        def model_identity(self) -> EmbeddingModelIdentity:
            return EmbeddingModelIdentity(
                provider_id="deterministic",
                model="deterministic-test-embedding",
                model_version="1.0.0",
                dimension=8,
            )

        def capabilities(self) -> EmbeddingProviderCapabilities:
            return EmbeddingProviderCapabilities(
                provider_id="deterministic",
                dimension=8,
                is_deterministic=True,
            )

        def health(self) -> EmbeddingProviderHealth:
            return EmbeddingProviderHealth(healthy=True)

        def embed_text(self, text: str, *, request_id: str = "single") -> EmbeddingResult:
            batch = self.embed_batch([EmbeddingRequest(request_id=request_id, text=text)])
            return batch.results[0]

        def embed_batch(self, requests: Sequence[EmbeddingRequest]) -> EmbeddingBatchResult:
            results = []
            failed = []
            diagnostics = []
            for request in requests:
                if "fail" in request.text:
                    failed.append(request.request_id)
                    diagnostics.append(
                        EmbeddingDiagnostic(
                            code="forced_failure",
                            message="forced",
                            request_id=request.request_id,
                            severity="error",
                        )
                    )
                    continue
                results.append(
                    EmbeddingResult(
                        request_id=request.request_id,
                        embedding=tuple([0.1] * 8),
                        dimension=8,
                        model_identity=self.model_identity(),
                        usage=EmbeddingUsage(input_characters=len(request.text)),
                    )
                )
            return EmbeddingBatchResult(
                results=tuple(results),
                failed_request_ids=tuple(failed),
                diagnostics=tuple(diagnostics),
            )

    store = InMemoryVectorStore()
    indexer = KnowledgeIndexer(
        embedding_provider=FlakyProvider(),  # type: ignore[arg-type]
        vector_store=store,
        embedding_settings=KnowledgeEmbeddingSettings(
            enabled=True,
            provider="deterministic",
            dimension=8,
            batch_size=10,
        ),
        indexing_settings=KnowledgeIndexingSettings(enabled=True),
    )
    chunks = (
        _chunk(document_id="kd:1", sequence=0, content="ok-one"),
        _chunk(document_id="kd:1", sequence=1, content="fail-me"),
    )
    result = indexer.index(KnowledgeIndexRequest(corpus=_corpus(chunks), scope=_scope()))
    assert result.status == KnowledgeIndexStatus.PARTIAL
    assert result.manifest.coverage.added == 1
    assert result.manifest.coverage.failed == 1
    assert len(store) == 1


def test_manifest_determinism_and_artifact(tmp_path) -> None:
    chunks = (
        _chunk(document_id="kd:1", sequence=0, content="a"),
        _chunk(document_id="kd:1", sequence=1, content="b"),
    )
    indexer, _store = _indexer()
    request = KnowledgeIndexRequest(corpus=_corpus(chunks), scope=_scope())
    left = indexer.index(request)
    right = indexer.index(request)
    assert left.manifest.fingerprint == right.manifest.fingerprint
    assert dumps_stable_json(left.manifest.model_dump(mode="json")) == dumps_stable_json(
        right.manifest.model_dump(mode="json")
    )
    path = write_knowledge_index_artifact(
        left,
        tmp_path,
        enabled=True,
        filename="repository-knowledge-index.json",
    )
    assert path is not None
    text = path.read_text(encoding="utf-8")
    assert "embedding" not in text or '"embedding_identity"' in text
    # Raw embedding arrays must not be persisted.
    assert "0.012" not in text
    assert left.manifest.entries[0].status == KnowledgeIndexEntryStatus.ADDED
