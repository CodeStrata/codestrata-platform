"""Assemble RetrievalContext from selected vector hits."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from codestrata_platform.rag.domain.retrieval import (
    RetrievalContext,
    RetrievalDiagnostic,
    RetrievalHit,
)
from codestrata_platform.rag.domain.vector import VectorSearchResult


def citation_label_for_rank(rank: int) -> str:
    """Deterministic citation label: SRC-001, SRC-002, …"""

    if rank <= 0:
        raise ValueError("rank must be positive")
    return f"SRC-{rank:03d}"


def _meta_str(meta: Mapping[str, Any], key: str) -> str | None:
    value = meta.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _meta_int(meta: Mapping[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = meta.get(key)
        if value is None:
            continue
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, str) and value.strip().lstrip("-").isdigit():
            return int(value.strip())
    return None


def build_traceability(meta: Mapping[str, Any]) -> dict[str, Any]:
    """Build citation-ready traceability from vector metadata."""

    payload = {
        "source_id": meta.get("traceability_source_id"),
        "parent_document_id": meta.get("parent_document_id") or meta.get("document_id"),
        "source_type": meta.get("source_type"),
        "repository_id": meta.get("repository_id"),
        "scan_id": meta.get("scan_id"),
        "branch": meta.get("branch"),
        "commit_sha": meta.get("commit_sha"),
        "file_path": meta.get("file_path"),
        "symbol_name": meta.get("symbol_name"),
        "finding_id": meta.get("finding_id"),
        "rule_id": meta.get("rule_id"),
        "evidence_id": meta.get("evidence_id"),
        "assessment_version": meta.get("assessment_version"),
        "report_section": meta.get("report_section"),
        "chunk_id": meta.get("chunk_id"),
        "document_id": meta.get("document_id"),
        "sequence": meta.get("chunk_sequence", meta.get("sequence")),
        "content_hash": meta.get("content_hash"),
    }
    return {key: value for key, value in payload.items() if value is not None}


def hit_from_search_result(
    result: VectorSearchResult,
    *,
    rank: int,
    include_content: bool,
    include_metadata: bool,
    include_traceability: bool,
) -> tuple[RetrievalHit, list[RetrievalDiagnostic]]:
    meta = result.record.metadata
    diagnostics: list[RetrievalDiagnostic] = []
    content = result.record.text if include_content else None
    if include_content and content is None:
        # Content may live only in chunks; vector records often omit text.
        content = _meta_str(meta, "content")
        if content is None:
            diagnostics.append(
                RetrievalDiagnostic(
                    code="missing_content",
                    message="vector record has no content text for citation body",
                    severity="info",
                    record_id=result.record_id,
                    chunk_id=_meta_str(meta, "chunk_id"),
                )
            )

    traceability = build_traceability(meta) if include_traceability else {}
    if include_traceability and not traceability:
        diagnostics.append(
            RetrievalDiagnostic(
                code="missing_traceability",
                message="vector record metadata lacks traceability fields",
                severity="info",
                record_id=result.record_id,
                chunk_id=_meta_str(meta, "chunk_id"),
            )
        )

    metadata_out = dict(meta) if include_metadata else {}
    hit = RetrievalHit(
        rank=rank,
        score=float(result.score),
        record_id=result.record_id,
        citation_label=citation_label_for_rank(rank),
        chunk_id=_meta_str(meta, "chunk_id"),
        document_id=_meta_str(meta, "document_id"),
        content=content,
        source_type=_meta_str(meta, "source_type"),
        intelligence_pack=_meta_str(meta, "intelligence_pack"),
        tenant_id=_meta_str(meta, "tenant_id"),
        repository_id=_meta_str(meta, "repository_id"),
        scan_id=_meta_str(meta, "scan_id"),
        branch=_meta_str(meta, "branch"),
        commit_sha=_meta_str(meta, "commit_sha"),
        file_path=_meta_str(meta, "file_path"),
        symbol_name=_meta_str(meta, "symbol_name"),
        finding_id=_meta_str(meta, "finding_id"),
        rule_id=_meta_str(meta, "rule_id"),
        severity=_meta_str(meta, "severity"),
        confidence=_meta_str(meta, "confidence"),
        sequence=_meta_int(meta, "chunk_sequence", "sequence"),
        content_hash=_meta_str(meta, "content_hash"),
        metadata=metadata_out,
        traceability=traceability,
    )
    return hit, diagnostics


def assemble_context(
    candidates: Sequence[VectorSearchResult],
    *,
    top_k: int,
    max_context_characters: int,
    include_content: bool,
    include_metadata: bool,
    include_traceability: bool,
) -> tuple[RetrievalContext, list[RetrievalDiagnostic], int]:
    """Select top_k hits under character budget; never mid-chunk truncate."""

    diagnostics: list[RetrievalDiagnostic] = []
    selected: list[RetrievalHit] = []
    used_chars = 0
    skipped_for_limit = 0
    rank = 1

    for candidate in candidates:
        if len(selected) >= top_k:
            break
        hit, hit_diags = hit_from_search_result(
            candidate,
            rank=rank,
            include_content=include_content,
            include_metadata=include_metadata,
            include_traceability=include_traceability,
        )
        diagnostics.extend(hit_diags)
        chunk_chars = len(hit.content or "")
        if include_content and chunk_chars > max_context_characters:
            skipped_for_limit += 1
            diagnostics.append(
                RetrievalDiagnostic(
                    code="context_limit_exclusion",
                    message=(
                        "chunk exceeds max_context_characters and cannot fit "
                        "without mid-chunk truncation"
                    ),
                    severity="warning",
                    record_id=hit.record_id,
                    chunk_id=hit.chunk_id,
                )
            )
            continue
        if include_content and used_chars + chunk_chars > max_context_characters:
            skipped_for_limit += 1
            diagnostics.append(
                RetrievalDiagnostic(
                    code="context_limit_exclusion",
                    message="chunk skipped because remaining context budget is insufficient",
                    severity="info",
                    record_id=hit.record_id,
                    chunk_id=hit.chunk_id,
                )
            )
            continue

        # Rebuild hit with correct rank after skips.
        if hit.rank != rank:
            hit, _ = hit_from_search_result(
                candidate,
                rank=rank,
                include_content=include_content,
                include_metadata=include_metadata,
                include_traceability=include_traceability,
            )
        selected.append(hit)
        used_chars += chunk_chars
        rank += 1

    context = RetrievalContext(
        hits=tuple(selected),
        character_count=used_chars,
        citation_labels=tuple(item.citation_label for item in selected),
    )
    return context, diagnostics, skipped_for_limit
