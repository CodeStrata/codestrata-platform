"""Bounded deterministic retrieval context assembly."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.application.retrieval.policies import (
    CONTEXT_POLICY_VERSION,
    DEFAULT_CONTEXT_MAX_TOKENS,
    HARD_CONTEXT_MAX_TOKENS,
)
from codestrata_platform.domain.retrieval.chunk import estimate_tokens
from codestrata_platform.domain.retrieval.errors import RetrievalLimitError
from codestrata_platform.domain.retrieval.result import RetrievalHit


@dataclass(frozen=True, slots=True)
class RetrievalCitation:
    chunk_id: str
    document_id: str
    canonical_type: str
    canonical_id: str
    source_references: tuple[str, ...]
    graph_node_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RetrievalContextItem:
    chunk_id: str
    document_id: str
    content_type: str
    canonical_type: str
    canonical_id: str
    text: str
    score: float
    citation: RetrievalCitation


@dataclass(frozen=True, slots=True)
class RetrievalContext:
    items: tuple[RetrievalContextItem, ...]
    token_estimate: int
    policy_version: str
    truncated: bool


class RetrievalContextAssembler:
    def __init__(self, *, max_tokens: int = DEFAULT_CONTEXT_MAX_TOKENS) -> None:
        if max_tokens < 1 or max_tokens > HARD_CONTEXT_MAX_TOKENS:
            raise RetrievalLimitError(
                f"max_tokens must be between 1 and {HARD_CONTEXT_MAX_TOKENS}",
                reason_code="context_token_limit_exceeded",
            )
        self._max_tokens = max_tokens

    def assemble(self, hits: tuple[RetrievalHit, ...]) -> RetrievalContext:
        seen_chunks: set[str] = set()
        seen_canonical: set[tuple[str, str]] = set()
        items: list[RetrievalContextItem] = []
        tokens = 0
        truncated = False
        type_counts: dict[str, int] = {}
        for hit in hits:
            chunk_key = hit.chunk_id.value
            if chunk_key in seen_chunks:
                continue
            canonical_key = (hit.canonical_type, hit.canonical_id)
            if canonical_key in seen_canonical and type_counts.get(hit.content_type.value, 0) >= 2:
                continue
            piece_tokens = estimate_tokens(hit.text)
            if tokens + piece_tokens > self._max_tokens:
                truncated = True
                break
            seen_chunks.add(chunk_key)
            seen_canonical.add(canonical_key)
            type_counts[hit.content_type.value] = type_counts.get(hit.content_type.value, 0) + 1
            tokens += piece_tokens
            citation = RetrievalCitation(
                chunk_id=hit.chunk_id.value,
                document_id=hit.document_id.value,
                canonical_type=hit.canonical_type,
                canonical_id=hit.canonical_id,
                source_references=tuple(
                    f"{item.source_kind}:{item.source_id}" for item in hit.source_references
                ),
                graph_node_ids=hit.graph_node_ids,
            )
            items.append(
                RetrievalContextItem(
                    chunk_id=hit.chunk_id.value,
                    document_id=hit.document_id.value,
                    content_type=hit.content_type.value,
                    canonical_type=hit.canonical_type,
                    canonical_id=hit.canonical_id,
                    text=hit.text,
                    score=hit.score.final_score,
                    citation=citation,
                )
            )
        return RetrievalContext(
            items=tuple(items),
            token_estimate=tokens,
            policy_version=CONTEXT_POLICY_VERSION,
            truncated=truncated,
        )
