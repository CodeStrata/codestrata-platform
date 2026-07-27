"""Retrieval query value objects."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.retrieval.errors import RetrievalLimitError
from codestrata_platform.domain.retrieval.taxonomy import RetrievalContentType, RetrievalMode

DEFAULT_TOP_K = 10
HARD_MAX_TOP_K = 100
DEFAULT_GRAPH_EXPANSION_DEPTH = 1
HARD_MAX_GRAPH_EXPANSION_DEPTH = 2


@dataclass(frozen=True, slots=True)
class RetrievalScope:
    organization_id: str
    workspace_id: str
    repository_id: str


@dataclass(frozen=True, slots=True)
class RetrievalQuery:
    query_text: str
    mode: RetrievalMode = RetrievalMode.HYBRID
    top_k: int = DEFAULT_TOP_K
    minimum_score: float = 0.0
    content_types: tuple[RetrievalContentType, ...] = ()
    canonical_types: tuple[str, ...] = ()
    canonical_ids: tuple[str, ...] = ()
    graph_node_ids: tuple[str, ...] = ()
    severity: str | None = None
    category: str | None = None
    production_scope: str | None = None
    include_source_references: bool = True
    include_score_breakdown: bool = True
    graph_expansion_depth: int = DEFAULT_GRAPH_EXPANSION_DEPTH

    def __post_init__(self) -> None:
        compact = self.query_text.strip()
        if not compact:
            raise InvalidValueError(
                "query_text must be non-blank",
                reason_code="empty_retrieval_query",
            )
        if self.top_k < 1 or self.top_k > HARD_MAX_TOP_K:
            raise RetrievalLimitError(
                f"top_k must be between 1 and {HARD_MAX_TOP_K}",
                reason_code="top_k_exceeded",
            )
        if self.minimum_score < 0 or self.minimum_score > 1:
            raise InvalidValueError(
                "minimum_score must be between 0 and 1",
                reason_code="invalid_minimum_score",
            )
        if (
            self.graph_expansion_depth < 0
            or self.graph_expansion_depth > HARD_MAX_GRAPH_EXPANSION_DEPTH
        ):
            raise RetrievalLimitError(
                f"graph_expansion_depth must be <= {HARD_MAX_GRAPH_EXPANSION_DEPTH}",
                reason_code="graph_expansion_depth_exceeded",
            )
        object.__setattr__(self, "query_text", compact)


@dataclass(frozen=True, slots=True)
class RetrievalScore:
    lexical_score: float = 0.0
    vector_score: float = 0.0
    graph_score: float = 0.0
    source_quality_score: float = 0.0
    final_score: float = 0.0
    policy_version: str = "1.0.0"

    def __post_init__(self) -> None:
        for name in (
            "lexical_score",
            "vector_score",
            "graph_score",
            "source_quality_score",
            "final_score",
        ):
            value = float(getattr(self, name))
            if value < 0:
                raise InvalidValueError(
                    f"{name} must be >= 0",
                    reason_code="invalid_retrieval_score",
                )
