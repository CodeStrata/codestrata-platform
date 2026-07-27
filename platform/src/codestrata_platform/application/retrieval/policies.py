"""Retrieval policies and configuration helpers."""

from __future__ import annotations

import os

from codestrata_platform.domain.retrieval.identifiers import DEFAULT_EMBEDDING_DIMENSION
from codestrata_platform.domain.retrieval.query import RetrievalScore

RETRIEVAL_SCHEMA_VERSION = "1.0"
CHUNKING_POLICY_VERSION = "1.0.0"
HYBRID_POLICY_VERSION = "1.0.0"
CONTEXT_POLICY_VERSION = "1.0.0"

INDEXING_ENABLED_ENV = "CODESTRATA_RETRIEVAL_INDEXING_ENABLED"
EMBEDDING_PROVIDER_ENV = "CODESTRATA_EMBEDDING_PROVIDER"
EMBEDDING_MODEL_ENV = "CODESTRATA_EMBEDDING_MODEL"
EMBEDDING_DIMENSION_ENV = "CODESTRATA_EMBEDDING_DIMENSION"

DEFAULT_CONTEXT_MAX_TOKENS = 6_000
HARD_CONTEXT_MAX_TOKENS = 12_000


def retrieval_indexing_enabled() -> bool:
    raw = os.environ.get(INDEXING_ENABLED_ENV, "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def configured_embedding_provider() -> str:
    raw = os.environ.get(EMBEDDING_PROVIDER_ENV, "deterministic").strip().lower()
    return raw or "deterministic"


def configured_embedding_model() -> str:
    return (
        os.environ.get(EMBEDDING_MODEL_ENV, "deterministic-test-embedding").strip()
        or "deterministic-test-embedding"
    )


def configured_embedding_dimension() -> int:
    raw = os.environ.get(EMBEDDING_DIMENSION_ENV, str(DEFAULT_EMBEDDING_DIMENSION)).strip()
    try:
        value = int(raw)
    except ValueError as error:
        raise ValueError("invalid_embedding_dimension") from error
    return value


class DefaultHybridRetrievalPolicy:
    """Explicit hybrid scoring weights."""

    version = HYBRID_POLICY_VERSION
    lexical_weight = 0.35
    vector_weight = 0.45
    graph_weight = 0.15
    source_quality_weight = 0.05

    def combine(
        self,
        *,
        lexical_score: float,
        vector_score: float,
        graph_score: float = 0.0,
        source_quality_score: float = 0.0,
    ) -> RetrievalScore:
        final = (
            self.lexical_weight * lexical_score
            + self.vector_weight * vector_score
            + self.graph_weight * graph_score
            + self.source_quality_weight * source_quality_score
        )
        return RetrievalScore(
            lexical_score=round(lexical_score, 6),
            vector_score=round(vector_score, 6),
            graph_score=round(graph_score, 6),
            source_quality_score=round(source_quality_score, 6),
            final_score=round(final, 6),
            policy_version=self.version,
        )


class DefaultCanonicalChunkingPolicy:
    version = CHUNKING_POLICY_VERSION
    target_min_tokens = 300
    target_max_tokens = 600
    hard_max_tokens = 1000
