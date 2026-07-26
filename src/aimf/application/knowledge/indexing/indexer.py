"""Knowledge indexing orchestration (Phase 5.3)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from aimf.application.knowledge.embedding.compatibility import (
    embedding_metadata_stamp,
)
from aimf.application.knowledge.embedding.protocol import EmbeddingProvider
from aimf.application.knowledge.indexing.mapping import (
    build_vector_record_for_chunk,
    chunk_matches_scope,
)
from aimf.application.knowledge.vector_store import VectorStore
from aimf.config.settings import KnowledgeEmbeddingSettings, KnowledgeIndexingSettings
from aimf.domain.knowledge.corpus import KnowledgeCorpus
from aimf.domain.knowledge.embedding import EmbeddingModelIdentity, EmbeddingRequest
from aimf.domain.knowledge.index_manifest import (
    KnowledgeIndexCoverage,
    KnowledgeIndexDiagnostic,
    KnowledgeIndexEntry,
    KnowledgeIndexEntryStatus,
    KnowledgeIndexManifest,
    KnowledgeIndexResult,
    KnowledgeIndexStatus,
    knowledge_index_result_payload,
)
from aimf.domain.knowledge.models import KnowledgeChunk
from aimf.domain.knowledge.schemas import VECTOR_RECORD_SCHEMA_VERSION
from aimf.domain.knowledge.vector import IndexScope, VectorRecord
from aimf.infrastructure.embedding.factory import create_embedding_provider
from aimf.infrastructure.vector_store.factory import create_vector_store
from aimf.services.artifact_serialization import dumps_stable_json

INDEX_ARTIFACT_FILENAME = "repository-knowledge-index.json"


@dataclass(frozen=True)
class KnowledgeIndexRequest:
    """In-memory indexing request over an existing KnowledgeCorpus."""

    corpus: KnowledgeCorpus
    scope: IndexScope
    prior_manifest: KnowledgeIndexManifest | None = None


class KnowledgeIndexer:
    """Embed eligible chunks and upsert VectorRecords into a VectorStore."""

    def __init__(
        self,
        *,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        embedding_settings: KnowledgeEmbeddingSettings | None = None,
        indexing_settings: KnowledgeIndexingSettings | None = None,
    ) -> None:
        self._embedding = embedding_provider
        self._store = vector_store
        self._embedding_settings = embedding_settings or KnowledgeEmbeddingSettings()
        self._indexing_settings = indexing_settings or KnowledgeIndexingSettings()

    def index(self, request: KnowledgeIndexRequest) -> KnowledgeIndexResult:
        """Run the indexing pipeline for one corpus and isolation scope."""

        if not self._indexing_settings.enabled:
            identity = self._embedding.model_identity()
            empty_manifest = KnowledgeIndexManifest.create(
                scope=request.scope,
                embedding_identity=identity,
                entries=(),
                coverage=KnowledgeIndexCoverage(),
                diagnostics=[
                    KnowledgeIndexDiagnostic(
                        code="indexing_disabled",
                        message="Knowledge indexing disabled by configuration",
                    )
                ],
                limitations=["knowledge.indexing.enabled=false"],
                corpus_id=request.corpus.corpus_id,
            )
            return KnowledgeIndexResult(
                status=KnowledgeIndexStatus.DISABLED,
                manifest=empty_manifest,
                diagnostics=empty_manifest.diagnostics,
                limitations=empty_manifest.limitations,
            )

        if not self._embedding_settings.enabled:
            identity = self._embedding.model_identity()
            empty_manifest = KnowledgeIndexManifest.create(
                scope=request.scope,
                embedding_identity=identity,
                entries=(),
                coverage=KnowledgeIndexCoverage(),
                diagnostics=[
                    KnowledgeIndexDiagnostic(
                        code="embedding_disabled",
                        message="Knowledge embedding disabled by configuration",
                    )
                ],
                limitations=["knowledge.embedding.enabled=false"],
                corpus_id=request.corpus.corpus_id,
            )
            return KnowledgeIndexResult(
                status=KnowledgeIndexStatus.DISABLED,
                manifest=empty_manifest,
                diagnostics=empty_manifest.diagnostics,
                limitations=empty_manifest.limitations,
            )

        identity = self._embedding.model_identity()
        self._validate_provider_settings(identity)

        chunks = tuple(
            sorted(
                request.corpus.chunks,
                key=lambda item: (item.document_id, item.sequence, item.chunk_id),
            )
        )
        diagnostics: list[KnowledgeIndexDiagnostic] = []
        limitations: list[str] = []

        if not chunks:
            manifest = KnowledgeIndexManifest.create(
                scope=request.scope,
                embedding_identity=identity,
                entries=(),
                coverage=KnowledgeIndexCoverage(),
                diagnostics=[
                    KnowledgeIndexDiagnostic(
                        code="empty_corpus",
                        message="KnowledgeCorpus contains no chunks to index",
                    )
                ],
                limitations=["empty corpus"],
                corpus_id=request.corpus.corpus_id,
            )
            return KnowledgeIndexResult(
                status=KnowledgeIndexStatus.EMPTY,
                manifest=manifest,
                diagnostics=manifest.diagnostics,
                limitations=manifest.limitations,
            )

        prior_by_key = self._prior_entries(request.prior_manifest, identity)
        compatible_prior = request.prior_manifest is not None and prior_by_key is not None

        if request.prior_manifest is not None and prior_by_key is None:
            diagnostics.append(
                KnowledgeIndexDiagnostic(
                    code="prior_manifest_incompatible",
                    message=(
                        "Prior manifest embedding identity or vector schema is incompatible; "
                        "all chunks will be re-embedded"
                    ),
                    severity="warning",
                )
            )
            limitations.append("prior manifest incompatible; full reindex")

        eligible: list[KnowledgeChunk] = []
        skipped_entries: list[KnowledgeIndexEntry] = []
        for chunk in chunks:
            if not chunk.content.strip():
                skipped_entries.append(
                    self._entry(
                        chunk,
                        status=KnowledgeIndexEntryStatus.SKIPPED,
                        record_id="skipped",
                    )
                )
                diagnostics.append(
                    KnowledgeIndexDiagnostic(
                        code="empty_chunk",
                        message="Skipped empty chunk content",
                        chunk_id=chunk.chunk_id,
                    )
                )
                continue
            if not chunk_matches_scope(
                chunk,
                tenant_id=request.scope.tenant_id,
                repository_id=request.scope.repository_id,
                scan_id=request.scope.scan_id,
            ):
                skipped_entries.append(
                    self._entry(
                        chunk,
                        status=KnowledgeIndexEntryStatus.SKIPPED,
                        record_id="skipped",
                    )
                )
                diagnostics.append(
                    KnowledgeIndexDiagnostic(
                        code="scope_mismatch",
                        message="Chunk metadata does not match declared IndexScope",
                        chunk_id=chunk.chunk_id,
                        severity="warning",
                    )
                )
                continue
            eligible.append(chunk)

        unchanged: list[tuple[KnowledgeChunk, KnowledgeIndexEntry]] = []
        to_embed: list[tuple[KnowledgeChunk, KnowledgeIndexEntryStatus]] = []
        stale_record_ids: list[str] = []
        for chunk in eligible:
            prior = (
                prior_by_key.get((chunk.document_id, chunk.sequence))
                if prior_by_key
                else None
            )
            if (
                compatible_prior
                and prior is not None
                and prior.chunk_fingerprint == chunk.fingerprint
                and prior.chunk_id == chunk.chunk_id
            ):
                unchanged.append((chunk, prior))
            elif prior is not None:
                to_embed.append((chunk, KnowledgeIndexEntryStatus.UPDATED))
                if prior.record_id.startswith("vr:"):
                    stale_record_ids.append(prior.record_id)
            else:
                to_embed.append((chunk, KnowledgeIndexEntryStatus.ADDED))

        current_keys = {(chunk.document_id, chunk.sequence) for chunk in eligible}
        removed_entries: list[KnowledgeIndexEntry] = []
        if prior_by_key is not None:
            for key, prior in sorted(prior_by_key.items()):
                if key not in current_keys:
                    removed_entries.append(
                        KnowledgeIndexEntry(
                            chunk_id=prior.chunk_id,
                            document_id=prior.document_id,
                            record_id=prior.record_id,
                            chunk_fingerprint=prior.chunk_fingerprint,
                            status=KnowledgeIndexEntryStatus.REMOVED,
                            sequence=prior.sequence,
                            source_type=prior.source_type,
                        )
                    )
                    if prior.record_id.startswith("vr:"):
                        stale_record_ids.append(prior.record_id)

        stale_deleted = 0
        if self._indexing_settings.delete_stale_records and stale_record_ids:
            # Unique preserve order
            unique_stale = list(dict.fromkeys(stale_record_ids))
            stale_deleted = self._store.delete_ids(unique_stale)
        elif stale_record_ids and not self._indexing_settings.delete_stale_records:
            diagnostics.append(
                KnowledgeIndexDiagnostic(
                    code="stale_records_retained",
                    message=(
                        f"{len(set(stale_record_ids))} stale record(s) retained because "
                        "delete_stale_records=false"
                    ),
                )
            )

        batch_size = self._embedding_settings.batch_size
        upserted_records: list[VectorRecord] = []
        result_entries: list[KnowledgeIndexEntry] = list(skipped_entries) + list(removed_entries)
        failed_count = 0
        batches = 0

        for chunk, prior in unchanged:
            result_entries.append(
                KnowledgeIndexEntry(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    record_id=prior.record_id,
                    chunk_fingerprint=chunk.fingerprint,
                    status=KnowledgeIndexEntryStatus.UNCHANGED,
                    sequence=chunk.sequence,
                    source_type=str(chunk.metadata.source_type)
                    if chunk.metadata.source_type
                    else None,
                )
            )

        for offset in range(0, len(to_embed), batch_size):
            batch = to_embed[offset : offset + batch_size]
            batches += 1
            requests = [
                EmbeddingRequest(request_id=chunk.chunk_id, text=chunk.content)
                for chunk, _status in batch
            ]
            try:
                batch_result = self._embedding.embed_batch(requests)
            except Exception as error:  # noqa: BLE001 - isolate batch failures
                failed_count += len(batch)
                for chunk, _status in batch:
                    result_entries.append(
                        self._entry(
                            chunk,
                            status=KnowledgeIndexEntryStatus.FAILED,
                            record_id="failed",
                        )
                    )
                    diagnostics.append(
                        KnowledgeIndexDiagnostic(
                            code="batch_failure",
                            message=f"Embedding batch failed: {error}",
                            chunk_id=chunk.chunk_id,
                            severity="error",
                        )
                    )
                continue

            success_by_id = {item.request_id: item for item in batch_result.results}
            failed_ids = set(batch_result.failed_request_ids)
            for diag in batch_result.diagnostics:
                diagnostics.append(
                    KnowledgeIndexDiagnostic(
                        code=diag.code,
                        message=diag.message,
                        chunk_id=diag.request_id,
                        severity=diag.severity,
                    )
                )

            batch_records: list[VectorRecord] = []
            for chunk, entry_status in batch:
                if chunk.chunk_id in failed_ids or chunk.chunk_id not in success_by_id:
                    failed_count += 1
                    result_entries.append(
                        self._entry(
                            chunk,
                            status=KnowledgeIndexEntryStatus.FAILED,
                            record_id="failed",
                        )
                    )
                    continue
                embedding = success_by_id[chunk.chunk_id].embedding
                if len(embedding) != identity.dimension:
                    failed_count += 1
                    result_entries.append(
                        self._entry(
                            chunk,
                            status=KnowledgeIndexEntryStatus.FAILED,
                            record_id="failed",
                        )
                    )
                    diagnostics.append(
                        KnowledgeIndexDiagnostic(
                            code="dimension_mismatch",
                            message=(
                                f"Embedding dimension {len(embedding)} does not match "
                                f"configured dimension {identity.dimension}"
                            ),
                            chunk_id=chunk.chunk_id,
                            severity="error",
                        )
                    )
                    continue
                record = build_vector_record_for_chunk(
                    chunk,
                    embedding=embedding,
                    namespace=request.scope.namespace,
                )
                # Ensure scope keys and embedding identity are present.
                meta = dict(record.metadata)
                meta.update(embedding_metadata_stamp(identity))
                if request.scope.tenant_id is not None:
                    meta["tenant_id"] = request.scope.tenant_id
                if request.scope.repository_id is not None:
                    meta["repository_id"] = request.scope.repository_id
                if request.scope.scan_id is not None:
                    meta["scan_id"] = request.scope.scan_id
                record = VectorRecord(
                    record_id=record.record_id,
                    schema_name=record.schema_name,
                    schema_version=record.schema_version,
                    namespace=record.namespace,
                    entity_id=record.entity_id,
                    embedding=record.embedding,
                    metadata=meta,
                    text=record.text,
                    fingerprint=record.fingerprint,
                )
                batch_records.append(record)
                result_entries.append(
                    KnowledgeIndexEntry(
                        chunk_id=chunk.chunk_id,
                        document_id=chunk.document_id,
                        record_id=record.record_id,
                        chunk_fingerprint=chunk.fingerprint,
                        status=entry_status,
                        sequence=chunk.sequence,
                        source_type=str(chunk.metadata.source_type)
                        if chunk.metadata.source_type
                        else None,
                    )
                )

            if batch_records:
                self._store.upsert(batch_records)
                upserted_records.extend(batch_records)

        coverage = KnowledgeIndexCoverage(
            chunk_count=len(chunks),
            vector_count=len(unchanged) + len(upserted_records),
            added=sum(1 for e in result_entries if e.status == KnowledgeIndexEntryStatus.ADDED),
            updated=sum(1 for e in result_entries if e.status == KnowledgeIndexEntryStatus.UPDATED),
            unchanged=sum(
                1 for e in result_entries if e.status == KnowledgeIndexEntryStatus.UNCHANGED
            ),
            removed=sum(1 for e in result_entries if e.status == KnowledgeIndexEntryStatus.REMOVED),
            skipped=sum(1 for e in result_entries if e.status == KnowledgeIndexEntryStatus.SKIPPED),
            failed=failed_count,
            stale_deleted=stale_deleted,
            batches=batches,
        )
        manifest = KnowledgeIndexManifest.create(
            scope=request.scope,
            embedding_identity=identity,
            entries=result_entries,
            coverage=coverage,
            diagnostics=diagnostics,
            limitations=limitations,
            corpus_id=request.corpus.corpus_id,
            vector_record_schema_version=VECTOR_RECORD_SCHEMA_VERSION,
        )

        if failed_count and (coverage.added or coverage.updated or coverage.unchanged):
            run_status = KnowledgeIndexStatus.PARTIAL
        elif failed_count and not (coverage.added or coverage.updated or coverage.unchanged):
            run_status = KnowledgeIndexStatus.FAILED
        else:
            run_status = KnowledgeIndexStatus.SUCCESS

        return KnowledgeIndexResult(
            status=run_status,
            manifest=manifest,
            indexed_record_ids=tuple(
                sorted(record.record_id for record in upserted_records)
            ),
            diagnostics=tuple(diagnostics),
            limitations=tuple(limitations),
        )

    def _validate_provider_settings(self, identity: EmbeddingModelIdentity) -> None:
        if identity.dimension != self._embedding_settings.dimension:
            raise ValueError(
                "embedding provider dimension does not match knowledge.embedding.dimension "
                f"({identity.dimension} != {self._embedding_settings.dimension})"
            )
        if identity.provider_id != self._embedding_settings.provider:
            raise ValueError(
                "embedding provider id does not match knowledge.embedding.provider "
                f"({identity.provider_id!r} != {self._embedding_settings.provider!r})"
            )

    def _prior_entries(
        self,
        prior: KnowledgeIndexManifest | None,
        identity: EmbeddingModelIdentity,
    ) -> dict[tuple[str, int], KnowledgeIndexEntry] | None:
        if prior is None:
            return None
        if not (
            prior.embedding_identity.provider_id == identity.provider_id
            and prior.embedding_identity.model == identity.model
            and prior.embedding_identity.model_version == identity.model_version
            and prior.embedding_identity.dimension == identity.dimension
            and prior.vector_record_schema_version == VECTOR_RECORD_SCHEMA_VERSION
        ):
            return None
        return {
            (entry.document_id, entry.sequence): entry
            for entry in prior.entries
            if entry.status
            not in {
                KnowledgeIndexEntryStatus.REMOVED,
                KnowledgeIndexEntryStatus.SKIPPED,
                KnowledgeIndexEntryStatus.FAILED,
            }
        }

    @staticmethod
    def _entry(
        chunk: KnowledgeChunk,
        *,
        status: KnowledgeIndexEntryStatus,
        record_id: str,
    ) -> KnowledgeIndexEntry:
        return KnowledgeIndexEntry(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            record_id=record_id,
            chunk_fingerprint=chunk.fingerprint,
            status=status,
            sequence=chunk.sequence,
            source_type=str(chunk.metadata.source_type) if chunk.metadata.source_type else None,
        )


def create_knowledge_indexer(
    *,
    embedding_settings: KnowledgeEmbeddingSettings | None = None,
    indexing_settings: KnowledgeIndexingSettings | None = None,
    vector_store: VectorStore | None = None,
    embedding_provider: EmbeddingProvider | None = None,
) -> KnowledgeIndexer:
    """Construct a KnowledgeIndexer with configured providers."""

    emb_settings = embedding_settings or KnowledgeEmbeddingSettings()
    idx_settings = indexing_settings or KnowledgeIndexingSettings()
    provider = embedding_provider or create_embedding_provider(emb_settings)
    store = vector_store or create_vector_store()
    return KnowledgeIndexer(
        embedding_provider=provider,
        vector_store=store,
        embedding_settings=emb_settings,
        indexing_settings=idx_settings,
    )


def write_knowledge_index_artifact(
    result: KnowledgeIndexResult,
    run_directory: Path,
    *,
    enabled: bool,
    filename: str = INDEX_ARTIFACT_FILENAME,
) -> Path | None:
    """Optionally write repository-knowledge-index.json (manifest + stats only)."""

    if not enabled:
        return None
    run_directory.mkdir(parents=True, exist_ok=True)
    path = run_directory / filename
    payload: Mapping[str, object] = {
        "status": result.status.value,
        "manifest": knowledge_index_result_payload(result)["manifest"],
        "coverage": result.manifest.coverage.model_dump(mode="json"),
        "indexed_record_count": len(result.indexed_record_ids),
        "diagnostic_count": len(result.diagnostics),
        "limitations": list(result.limitations),
    }
    text = dumps_stable_json(dict(payload))
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
    return path
