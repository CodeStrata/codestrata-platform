"""Deterministic retrieval deduplication and diversity controls."""

from __future__ import annotations

from collections.abc import Sequence

from aimf.domain.knowledge.vector import VectorSearchResult


def _identity_keys(hit: VectorSearchResult) -> tuple[str, ...]:
    meta = hit.record.metadata
    keys: list[str] = []
    chunk_id = meta.get("chunk_id")
    if chunk_id is not None:
        keys.append(f"chunk:{chunk_id}")
    content_hash = meta.get("content_hash")
    if content_hash is not None:
        keys.append(f"hash:{content_hash}")
    document_id = meta.get("document_id")
    sequence = meta.get("chunk_sequence", meta.get("sequence"))
    if document_id is not None and sequence is not None:
        keys.append(f"docseq:{document_id}:{sequence}")
    keys.append(f"record:{hit.record_id}")
    return tuple(keys)


def deduplicate_hits(
    hits: Sequence[VectorSearchResult],
) -> tuple[list[VectorSearchResult], int]:
    """Keep highest score per identity; ties by record_id ascending.

    Input should already be sorted by (-score, record_id). Walking in order and
    keeping the first unseen identity retains the best score deterministically.
    """

    ordered = sorted(hits, key=lambda item: (-item.score, item.record_id))
    seen: set[str] = set()
    kept: list[VectorSearchResult] = []
    removed = 0
    for hit in ordered:
        identities = _identity_keys(hit)
        if any(key in seen for key in identities):
            removed += 1
            continue
        for key in identities:
            seen.add(key)
        kept.append(hit)
    return kept, removed


def apply_diversity_limits(
    hits: Sequence[VectorSearchResult],
    *,
    max_chunks_per_document: int,
    max_chunks_per_file: int,
    max_chunks_per_source_type: int,
) -> tuple[list[VectorSearchResult], int]:
    """Cap hits per document / file / source_type using deterministic order."""

    doc_counts: dict[str, int] = {}
    file_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    kept: list[VectorSearchResult] = []
    excluded = 0
    for hit in hits:
        meta = hit.record.metadata
        document_id = str(meta.get("document_id") or "")
        file_path = str(meta.get("file_path") or "")
        source_type = str(meta.get("source_type") or "")

        if document_id and doc_counts.get(document_id, 0) >= max_chunks_per_document:
            excluded += 1
            continue
        if file_path and file_counts.get(file_path, 0) >= max_chunks_per_file:
            excluded += 1
            continue
        if source_type and source_counts.get(source_type, 0) >= max_chunks_per_source_type:
            excluded += 1
            continue

        kept.append(hit)
        if document_id:
            doc_counts[document_id] = doc_counts.get(document_id, 0) + 1
        if file_path:
            file_counts[file_path] = file_counts.get(file_path, 0) + 1
        if source_type:
            source_counts[source_type] = source_counts.get(source_type, 0) + 1
    return kept, excluded
