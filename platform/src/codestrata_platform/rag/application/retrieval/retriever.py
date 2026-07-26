"""RepositoryRetriever — provider-neutral retrieval over VectorStore (Phase 5.5 / 5.9)."""

from __future__ import annotations

import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from codestrata.config.settings import KnowledgeEmbeddingSettings, KnowledgeRetrievalSettings
from codestrata.security.database_url import sanitize_exception_message
from codestrata.services.artifact_serialization import dumps_stable_json
from codestrata_platform.rag.application.embedding.compatibility import (
    EmbeddingIndexCompatibilityError,
    assert_index_compatible,
)
from codestrata_platform.rag.application.embedding.protocol import EmbeddingProvider
from codestrata_platform.rag.application.retrieval.context import assemble_context
from codestrata_platform.rag.application.retrieval.deduplication import (
    apply_diversity_limits,
    deduplicate_hits,
)
from codestrata_platform.rag.application.retrieval.filtering import (
    FilterValidationError,
    build_vector_filter,
    post_filter_hits,
)
from codestrata_platform.rag.application.retrieval.fusion import fuse_with_components
from codestrata_platform.rag.application.retrieval.lexical import lexical_search_store
from codestrata_platform.rag.application.retrieval.query_preparation import (
    QueryPreparationError,
    prepare_retrieval_query,
)
from codestrata_platform.rag.application.vector_store import VectorStore
from codestrata_platform.rag.domain.retrieval import (
    RetrievalCoverage,
    RetrievalDiagnostic,
    RetrievalRequest,
    RetrievalResult,
    RetrievalStatus,
    build_result_fingerprint,
    retrieval_result_payload,
)
from codestrata_platform.rag.domain.vector import VectorQuery, VectorSearchResult
from codestrata_platform.rag.embedding import create_embedding_provider
from codestrata_platform.rag.vector_store import create_vector_store

RETRIEVAL_ARTIFACT_FILENAME = "repository-retrieval-result.json"

DEFAULT_LIMITATIONS = (
    "Retrieval returns grounded knowledge context only; it does not generate answers.",
    "Supported modes: vector, lexical, hybrid (Reciprocal Rank Fusion). "
    "No graph expansion or learned reranking.",
    "DeterministicEmbeddingProvider is for tests/dogfood, not production semantics.",
)


class RepositoryRetriever:
    """Search indexed knowledge chunks and assemble grounded retrieval context.

    Accepts an existing EmbeddingProvider and VectorStore. Does not project,
    chunk, index, open DB connections, read source files, or invoke LLMs.
    """

    def __init__(
        self,
        *,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        retrieval_settings: KnowledgeRetrievalSettings | None = None,
        embedding_settings: KnowledgeEmbeddingSettings | None = None,
    ) -> None:
        self._embedding = embedding_provider
        self._store = vector_store
        self._settings = retrieval_settings or KnowledgeRetrievalSettings()
        self._embedding_settings = embedding_settings or KnowledgeEmbeddingSettings()

    def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        settings = self._settings
        started = time.perf_counter()
        if not settings.enabled:
            return RetrievalResult(
                status=RetrievalStatus.DISABLED,
                scope=request.scope,
                diagnostics=(
                    RetrievalDiagnostic(
                        code="retrieval_disabled",
                        message="knowledge.retrieval.enabled is false",
                        severity="info",
                    ),
                ),
                limitations=DEFAULT_LIMITATIONS,
            )

        mode = settings.mode
        diagnostics: list[RetrievalDiagnostic] = []
        try:
            prepared = prepare_retrieval_query(
                request.query,
                max_query_characters=request.max_query_characters,
            )
        except QueryPreparationError as exc:
            return RetrievalResult(
                status=RetrievalStatus.FAILED,
                scope=request.scope,
                diagnostics=(exc.as_diagnostic(),),
                limitations=DEFAULT_LIMITATIONS,
            )

        try:
            vector_filter = build_vector_filter(request.scope, request.filters)
        except FilterValidationError as exc:
            return RetrievalResult(
                status=RetrievalStatus.FAILED,
                query=prepared,
                scope=request.scope,
                diagnostics=(exc.as_diagnostic(),),
                limitations=DEFAULT_LIMITATIONS,
            )

        vector_hits: tuple[VectorSearchResult, ...] = ()
        lexical_hits: tuple[VectorSearchResult, ...] = ()
        score_components: dict[str, dict[str, float]] = {}

        if mode in {"vector", "hybrid"}:
            try:
                vector_hits = self._vector_search(
                    prepared.normalized,
                    request=request,
                    vector_filter=vector_filter,
                )
            except EmbeddingIndexCompatibilityError as exc:
                return RetrievalResult(
                    status=RetrievalStatus.FAILED,
                    query=prepared,
                    scope=request.scope,
                    diagnostics=(
                        RetrievalDiagnostic(
                            code="embedding_index_incompatible",
                            message=sanitize_exception_message(str(exc)),
                            severity="error",
                        ),
                    ),
                    limitations=DEFAULT_LIMITATIONS,
                )
            except Exception as exc:  # noqa: BLE001
                message = sanitize_exception_message(str(exc))
                code = (
                    "dimension_mismatch"
                    if "dimension" in message.lower()
                    else (
                        "embedding_failure"
                        if "embed" in message.lower()
                        else "vector_store_failure"
                    )
                )
                return RetrievalResult(
                    status=RetrievalStatus.FAILED,
                    query=prepared,
                    scope=request.scope,
                    diagnostics=(
                        RetrievalDiagnostic(
                            code=code, message=message, severity="error"
                        ),
                    ),
                    limitations=DEFAULT_LIMITATIONS,
                )

        if mode in {"lexical", "hybrid"}:
            try:
                lexical_hits = lexical_search_store(
                    store=self._store,
                    query=prepared.normalized,
                    top_k=request.candidate_limit,
                    vector_filter=vector_filter,
                    fetch_limit=max(request.candidate_limit * 20, 200),
                )
            except Exception as exc:  # noqa: BLE001
                return RetrievalResult(
                    status=RetrievalStatus.FAILED,
                    query=prepared,
                    scope=request.scope,
                    diagnostics=(
                        RetrievalDiagnostic(
                            code="lexical_retrieval_failure",
                            message=sanitize_exception_message(str(exc)),
                            severity="error",
                        ),
                    ),
                    limitations=DEFAULT_LIMITATIONS,
                )

        if mode == "vector":
            raw_hits = vector_hits
            # Cosine minimum_score applies only to dense vector mode.
            scored = [hit for hit in raw_hits if hit.score >= request.minimum_score]
            score_excluded = len(raw_hits) - len(scored)
            fused_count = len(scored)
        elif mode == "lexical":
            raw_hits = lexical_hits
            scored = list(raw_hits)
            score_excluded = 0
            fused_count = len(scored)
        else:
            fused, score_components = fuse_with_components(
                {"vector": vector_hits, "lexical": lexical_hits},
                weights={
                    "vector": settings.vector_weight,
                    "lexical": settings.lexical_weight,
                },
                k=settings.rrf_k,
            )
            raw_hits = fused
            scored = list(fused)
            score_excluded = 0
            fused_count = len(fused)

        candidates_returned = len(vector_hits) + len(lexical_hits)
        if mode == "hybrid":
            candidates_returned = len(vector_hits) + len(lexical_hits)

        filtered, filter_excluded = post_filter_hits(
            scored,
            scope=request.scope,
            filters=request.filters,
        )
        filter_excluded += score_excluded

        clean: list[VectorSearchResult] = []
        query_identity = self._embedding.model_identity()
        for hit in filtered:
            try:
                meta = hit.record.metadata
                if mode in {"vector", "hybrid"}:
                    assert_index_compatible(
                        query_identity=query_identity,
                        record_metadata=dict(meta) if meta else None,
                    )
                clean.append(hit)
            except EmbeddingIndexCompatibilityError as exc:
                return RetrievalResult(
                    status=RetrievalStatus.FAILED,
                    query=prepared,
                    scope=request.scope,
                    diagnostics=(
                        RetrievalDiagnostic(
                            code="embedding_index_incompatible",
                            message=sanitize_exception_message(str(exc)),
                            severity="error",
                            record_id=getattr(hit, "record_id", None),
                        ),
                    ),
                    limitations=DEFAULT_LIMITATIONS,
                )
            except Exception as exc:  # noqa: BLE001
                diagnostics.append(
                    RetrievalDiagnostic(
                        code="malformed_record",
                        message=sanitize_exception_message(str(exc)),
                        severity="warning",
                        record_id=getattr(hit, "record_id", None),
                    )
                )

        deduped, duplicates_removed = deduplicate_hits(clean)
        diversified, diversity_excluded = apply_diversity_limits(
            deduped,
            max_chunks_per_document=request.max_chunks_per_document,
            max_chunks_per_file=request.max_chunks_per_file,
            max_chunks_per_source_type=request.max_chunks_per_source_type,
        )

        effective_top_k = request.top_k
        context, ctx_diags, context_excluded = assemble_context(
            diversified,
            top_k=effective_top_k,
            max_context_characters=request.max_context_characters,
            include_content=request.include_content,
            include_metadata=request.include_metadata,
            include_traceability=request.include_traceability,
        )
        diagnostics.extend(ctx_diags)

        latency_ms = int((time.perf_counter() - started) * 1000)
        diagnostics.insert(
            0,
            RetrievalDiagnostic(
                code="retrieval_mode",
                message=mode,
                severity="info",
            ),
        )
        diagnostics.append(
            RetrievalDiagnostic(
                code="retrieval_stats",
                message=(
                    f"mode={mode} vector_candidates={len(vector_hits)} "
                    f"lexical_candidates={len(lexical_hits)} "
                    f"fused_candidates={fused_count} "
                    f"final_result_count={len(context.hits)} "
                    f"latency_ms={latency_ms} "
                    f"vector_weight={settings.vector_weight} "
                    f"lexical_weight={settings.lexical_weight}"
                ),
                severity="info",
            )
        )
        if score_components and context.hits:
            # Emit compact score-component diagnostics for top fused hits only.
            for context_hit in context.hits[:5]:
                comps = score_components.get(context_hit.record_id, {})
                if not comps:
                    continue
                parts = " ".join(
                    f"{key}={value:.6f}"
                    for key, value in sorted(comps.items())
                )
                diagnostics.append(
                    RetrievalDiagnostic(
                        code="score_components",
                        message=f"record_id={context_hit.record_id} {parts}",
                        severity="info",
                        record_id=context_hit.record_id,
                    )
                )

        coverage = _build_coverage(
            candidates_requested=request.candidate_limit,
            candidates_returned=candidates_returned
            if mode != "hybrid"
            else max(len(vector_hits), len(lexical_hits), fused_count),
            duplicates_removed=duplicates_removed,
            filter_exclusions=filter_excluded,
            diversity_exclusions=diversity_excluded,
            context_limit_exclusions=context_excluded,
            hits=context.hits,
            retrieval_mode=mode,
            vector_candidates=len(vector_hits),
            lexical_candidates=len(lexical_hits),
            fused_candidates=fused_count,
            latency_ms=latency_ms,
        )

        if not context.hits:
            status = RetrievalStatus.EMPTY
        elif (
            context_excluded
            or diversity_excluded
            or any(d.code in {"missing_content", "malformed_record"} for d in diagnostics)
        ):
            status = RetrievalStatus.PARTIAL
        else:
            status = RetrievalStatus.SUCCESS

        fingerprint = build_result_fingerprint(
            query_fingerprint=prepared.fingerprint,
            scope=request.scope,
            hit_record_ids=[hit.record_id for hit in context.hits],
            status=status,
        )
        return RetrievalResult(
            status=status,
            query=prepared,
            scope=request.scope,
            context=context,
            coverage=coverage,
            diagnostics=tuple(diagnostics),
            limitations=DEFAULT_LIMITATIONS,
            fingerprint=fingerprint,
        )

    def _vector_search(
        self,
        normalized_query: str,
        *,
        request: RetrievalRequest,
        vector_filter: Any,
    ) -> tuple[VectorSearchResult, ...]:
        expected_dim = self._embedding.model_identity().dimension
        if (
            self._embedding_settings.dimension
            and expected_dim != self._embedding_settings.dimension
        ):
            raise ValueError(
                "embedding provider dimension does not match "
                f"knowledge.embedding.dimension ({expected_dim} != "
                f"{self._embedding_settings.dimension})"
            )
        embedded = self._embedding.embed_text(
            normalized_query,
            request_id=f"retrieval:{normalized_query[:24]}",
        )
        if len(embedded.embedding) != expected_dim:
            raise ValueError(
                "query embedding dimension mismatch: "
                f"got {len(embedded.embedding)}, expected {expected_dim}"
            )
        raw_hits = self._store.search(
            VectorQuery(
                embedding=embedded.embedding,
                top_k=request.candidate_limit,
                filter=vector_filter,
                text_query=normalized_query,
            )
        )
        # Compatibility checked later per-hit; preflight first hit when present.
        if raw_hits:
            assert_index_compatible(
                query_identity=self._embedding.model_identity(),
                record_metadata=dict(raw_hits[0].record.metadata or {}),
            )
        return tuple(raw_hits)


def _build_coverage(
    *,
    candidates_requested: int,
    candidates_returned: int,
    duplicates_removed: int,
    filter_exclusions: int,
    diversity_exclusions: int,
    context_limit_exclusions: int,
    hits: Sequence[Any],
    retrieval_mode: str | None = None,
    vector_candidates: int = 0,
    lexical_candidates: int = 0,
    fused_candidates: int = 0,
    latency_ms: int = 0,
) -> RetrievalCoverage:
    source_types = sorted(
        {h.source_type for h in hits if getattr(h, "source_type", None)}
    )
    packs = sorted(
        {h.intelligence_pack for h in hits if getattr(h, "intelligence_pack", None)}
    )
    files = sorted({h.file_path for h in hits if getattr(h, "file_path", None)})
    findings = sorted({h.finding_id for h in hits if getattr(h, "finding_id", None)})
    scans = sorted({h.scan_id for h in hits if getattr(h, "scan_id", None)})
    return RetrievalCoverage(
        candidates_requested=candidates_requested,
        candidates_returned=candidates_returned,
        duplicates_removed=duplicates_removed,
        filter_exclusions=filter_exclusions,
        diversity_exclusions=diversity_exclusions,
        context_limit_exclusions=context_limit_exclusions,
        final_hit_count=len(hits),
        retrieval_mode=retrieval_mode,
        vector_candidates=vector_candidates,
        lexical_candidates=lexical_candidates,
        fused_candidates=fused_candidates,
        latency_ms=latency_ms,
        source_types=tuple(source_types),
        intelligence_packs=tuple(packs),
        files=tuple(files),
        findings=tuple(findings),
        scans=tuple(scans),
    )


def create_repository_retriever(
    *,
    retrieval_settings: KnowledgeRetrievalSettings | None = None,
    embedding_settings: KnowledgeEmbeddingSettings | None = None,
    vector_store: VectorStore | None = None,
    embedding_provider: EmbeddingProvider | None = None,
) -> RepositoryRetriever:
    """Construct a RepositoryRetriever with configured providers."""

    ret_settings = retrieval_settings or KnowledgeRetrievalSettings()
    emb_settings = embedding_settings or KnowledgeEmbeddingSettings()
    provider = embedding_provider or create_embedding_provider(emb_settings)
    store = vector_store or create_vector_store()
    return RepositoryRetriever(
        embedding_provider=provider,
        vector_store=store,
        retrieval_settings=ret_settings,
        embedding_settings=emb_settings,
    )


def write_retrieval_result_artifact(
    result: RetrievalResult,
    run_directory: Path,
    *,
    enabled: bool,
    filename: str = RETRIEVAL_ARTIFACT_FILENAME,
    include_content: bool = True,
) -> Path | None:
    """Optionally write repository-retrieval-result.json (no embedding arrays)."""

    if not enabled:
        return None
    run_directory.mkdir(parents=True, exist_ok=True)
    path = run_directory / filename
    payload = retrieval_result_payload(result)
    if not include_content:
        for hit in payload.get("context", {}).get("hits", []):
            hit.pop("content", None)
    _strip_embeddings(payload)
    text = dumps_stable_json(payload)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
    return path


def _strip_embeddings(payload: Any) -> None:
    if isinstance(payload, dict):
        payload.pop("embedding", None)
        payload.pop("embeddings", None)
        for value in payload.values():
            _strip_embeddings(value)
    elif isinstance(payload, list):
        for item in payload:
            _strip_embeddings(item)
