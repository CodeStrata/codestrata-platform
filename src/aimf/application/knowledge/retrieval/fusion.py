"""Deterministic hybrid fusion (Reciprocal Rank Fusion) — Phase 5.9."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from aimf.domain.knowledge.vector import VectorRecord, VectorSearchResult

DEFAULT_RRF_K = 60


def reciprocal_rank_fusion(
    ranked_lists: Mapping[str, Sequence[VectorSearchResult]],
    *,
    weights: Mapping[str, float],
    k: int = DEFAULT_RRF_K,
) -> tuple[VectorSearchResult, ...]:
    """Fuse ranked lists with weighted Reciprocal Rank Fusion.

    ``score(d) = sum_i weight_i / (k + rank_i(d))`` where ranks are 1-based.
    Duplicate ``record_id`` values across lists collapse to one fused hit.
    Stable ordering: fused score descending, then ``record_id`` ascending.
    """

    if k <= 0:
        raise ValueError("rrf k must be positive")
    scores: dict[str, float] = {}
    records: dict[str, VectorRecord] = {}
    components: dict[str, dict[str, float]] = {}

    for list_name, hits in ranked_lists.items():
        weight = float(weights.get(list_name, 1.0))
        if weight == 0.0:
            continue
        for rank, hit in enumerate(hits, start=1):
            contribution = weight / float(k + rank)
            scores[hit.record_id] = scores.get(hit.record_id, 0.0) + contribution
            records[hit.record_id] = hit.record
            bucket = components.setdefault(hit.record_id, {})
            bucket[list_name] = bucket.get(list_name, 0.0) + contribution
            # Preserve best source score under a namespaced key for diagnostics.
            bucket[f"{list_name}_rank"] = float(rank)
            bucket[f"{list_name}_source_score"] = float(hit.score)

    fused: list[VectorSearchResult] = []
    for record_id, score in scores.items():
        fused.append(
            VectorSearchResult(
                record_id=record_id,
                score=score,
                record=records[record_id],
            )
        )
    fused.sort(key=lambda item: (-item.score, item.record_id))
    # Attach component map on metadata copy for diagnostics (non-persistent).
    # Callers that need components can use fuse_with_components.
    return tuple(fused)


def fuse_with_components(
    ranked_lists: Mapping[str, Sequence[VectorSearchResult]],
    *,
    weights: Mapping[str, float],
    k: int = DEFAULT_RRF_K,
) -> tuple[tuple[VectorSearchResult, ...], dict[str, dict[str, float]]]:
    """RRF fusion plus per-record score component map for diagnostics."""

    if k <= 0:
        raise ValueError("rrf k must be positive")
    scores: dict[str, float] = {}
    records: dict[str, VectorRecord] = {}
    components: dict[str, dict[str, float]] = {}

    for list_name, hits in ranked_lists.items():
        weight = float(weights.get(list_name, 1.0))
        if weight == 0.0:
            continue
        for rank, hit in enumerate(hits, start=1):
            contribution = weight / float(k + rank)
            scores[hit.record_id] = scores.get(hit.record_id, 0.0) + contribution
            records[hit.record_id] = hit.record
            bucket = components.setdefault(hit.record_id, {})
            bucket[list_name] = bucket.get(list_name, 0.0) + contribution
            bucket[f"{list_name}_rank"] = float(rank)
            bucket[f"{list_name}_source_score"] = float(hit.score)

    fused: list[VectorSearchResult] = []
    for record_id, score in scores.items():
        fused.append(
            VectorSearchResult(
                record_id=record_id,
                score=score,
                record=records[record_id],
            )
        )
    fused.sort(key=lambda item: (-item.score, item.record_id))
    return tuple(fused), components


__all__ = [
    "DEFAULT_RRF_K",
    "fuse_with_components",
    "reciprocal_rank_fusion",
]
