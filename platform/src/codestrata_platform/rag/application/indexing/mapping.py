"""Map KnowledgeChunk instances to VectorRecord payloads."""

from __future__ import annotations

from typing import Any

from codestrata_platform.rag.domain.models import KnowledgeChunk
from codestrata_platform.rag.domain.vector import VectorRecord


def chunk_vector_metadata(chunk: KnowledgeChunk) -> dict[str, Any]:
    """Build filterable vector metadata retained for future citations."""

    meta = chunk.metadata
    trace = chunk.traceability
    payload: dict[str, Any] = {
        "chunk_id": chunk.chunk_id,
        "document_id": chunk.document_id,
        "chunk_sequence": chunk.sequence,
        "chunk_fingerprint": chunk.fingerprint,
        "tenant_id": meta.tenant_id,
        "repository_id": meta.repository_id,
        "scan_id": meta.scan_id,
        "branch": meta.branch,
        "commit_sha": meta.commit_sha,
        "source_type": str(meta.source_type) if meta.source_type else str(
            trace.source.source_type
        ),
        "intelligence_pack": meta.intelligence_pack,
        "assessment_version": meta.assessment_version or trace.assessment_version,
        "finding_id": meta.finding_id or trace.source.finding_id,
        "rule_id": meta.rule_id or trace.source.rule_id,
        "severity": meta.severity,
        "confidence": meta.confidence,
        "file_path": meta.file_path or trace.source.file_path,
        "symbol_name": meta.symbol_name,
        "content_hash": meta.content_hash,
        "traceability_source_id": trace.source_id,
        "parent_document_id": trace.parent_document_id or chunk.document_id,
    }
    # Drop Nones for compact filtering; keep explicit False/0.
    return {key: value for key, value in payload.items() if value is not None}


def chunk_matches_scope(chunk: KnowledgeChunk, *, tenant_id: str | None,
                        repository_id: str | None, scan_id: str | None) -> bool:
    """Return True when chunk metadata matches the declared isolation scope."""

    meta = chunk.metadata
    if tenant_id is not None and meta.tenant_id != tenant_id:
        return False
    if repository_id is not None and meta.repository_id != repository_id:
        return False
    if scan_id is not None and meta.scan_id != scan_id:
        return False
    return True


def build_vector_record_for_chunk(
    chunk: KnowledgeChunk,
    *,
    embedding: tuple[float, ...],
    namespace: str = "default",
) -> VectorRecord:
    """Construct a deterministic VectorRecord for one knowledge chunk."""

    return VectorRecord.create(
        entity_id=chunk.chunk_id,
        embedding=embedding,
        metadata=chunk_vector_metadata(chunk),
        text=chunk.content,
        namespace=namespace,
    )
