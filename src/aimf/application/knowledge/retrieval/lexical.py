"""Deterministic lexical retrieval over indexed chunk text (Phase 5.9)."""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Sequence

from aimf.domain.knowledge.vector import VectorFilter, VectorRecord, VectorSearchResult

_TOKEN = re.compile(r"[a-z0-9_]{2,}", re.IGNORECASE)


def tokenize(text: str) -> tuple[str, ...]:
    """Lowercase alphanumeric tokens (stable, deterministic)."""

    return tuple(_TOKEN.findall(text.lower()))


def lexical_search(
    query: str,
    records: Sequence[VectorRecord],
    *,
    top_k: int,
) -> tuple[VectorSearchResult, ...]:
    """Rank records by deterministic BM25-lite lexical relevance.

    Stable ordering: score descending, then ``record_id`` ascending.
    Records without text are ignored.
    """

    if top_k <= 0:
        raise ValueError("top_k must be positive")
    query_tokens = tokenize(query)
    if not query_tokens:
        return ()

    docs: list[tuple[VectorRecord, tuple[str, ...]]] = []
    for record in records:
        text = (record.text or "").strip()
        if not text:
            continue
        docs.append((record, tokenize(text)))
    if not docs:
        return ()

    query_terms = tuple(dict.fromkeys(query_tokens))  # stable unique order
    doc_count = len(docs)
    df: Counter[str] = Counter()
    for _, tokens in docs:
        present = set(tokens)
        for term in query_terms:
            if term in present:
                df[term] += 1

    avgdl = sum(len(tokens) for _, tokens in docs) / float(doc_count)
    k1 = 1.2
    b = 0.75
    hits: list[VectorSearchResult] = []
    for record, tokens in docs:
        tf = Counter(tokens)
        doc_len = len(tokens) or 1
        score = 0.0
        matched = 0
        for term in query_terms:
            frequency = tf.get(term, 0)
            if frequency <= 0:
                continue
            matched += 1
            idf = math.log(1.0 + (doc_count - df[term] + 0.5) / (df[term] + 0.5))
            denom = frequency + k1 * (1.0 - b + b * doc_len / max(avgdl, 1.0))
            score += idf * ((frequency * (k1 + 1.0)) / denom)
        if matched == 0 or score <= 0.0:
            continue
        coverage = matched / float(len(query_terms))
        # Coverage boost keeps short exact matches competitive without nondeterminism.
        final = score * (0.5 + 0.5 * coverage)
        hits.append(
            VectorSearchResult(
                record_id=record.record_id,
                score=final,
                record=record,
            )
        )
    hits.sort(key=lambda item: (-item.score, item.record_id))
    return tuple(hits[:top_k])


def lexical_search_store(
    *,
    store: object,
    query: str,
    top_k: int,
    vector_filter: VectorFilter | None,
    fetch_limit: int,
) -> tuple[VectorSearchResult, ...]:
    """Fetch filtered records from a VectorStore and score them lexically."""

    fetch = getattr(store, "fetch_filtered", None)
    if not callable(fetch):
        raise RuntimeError(
            "vector store does not support fetch_filtered required for lexical retrieval"
        )
    records = fetch(
        vector_filter,
        limit=max(fetch_limit, top_k),
        require_text=True,
    )
    return lexical_search(query, records, top_k=top_k)


__all__ = [
    "lexical_search",
    "lexical_search_store",
    "tokenize",
]
