"""Answer retrieval strategy selection."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.application.answering.policies import (
    DEFAULT_TOP_K,
    RETRIEVAL_STRATEGY_VERSION,
    STRATEGY_CONTENT_TYPES,
    clamp_top_k,
)
from codestrata_platform.domain.answering.lifecycle import QuestionType
from codestrata_platform.domain.answering.question import QuestionScope
from codestrata_platform.domain.retrieval.query import HARD_MAX_GRAPH_EXPANSION_DEPTH
from codestrata_platform.domain.retrieval.taxonomy import RetrievalContentType, RetrievalMode


@dataclass(frozen=True, slots=True)
class AnswerRetrievalPlan:
    mode: RetrievalMode
    top_k: int
    content_types: tuple[RetrievalContentType, ...]
    canonical_ids: tuple[str, ...]
    graph_node_ids: tuple[str, ...]
    graph_expansion_depth: int
    policy_version: str


class DefaultAnswerRetrievalStrategy:
    version = RETRIEVAL_STRATEGY_VERSION

    def plan(
        self,
        *,
        question_type: QuestionType,
        scope: QuestionScope,
        top_k: int | None = None,
    ) -> AnswerRetrievalPlan:
        content_types = scope.content_types or STRATEGY_CONTENT_TYPES.get(question_type, ())
        depth = 1
        if question_type in {
            QuestionType.COMPONENT_IMPACT,
            QuestionType.TECHNOLOGY_IMPACT,
            QuestionType.DEPENDENCY_EXPLANATION,
            QuestionType.TRACEABILITY_EXPLANATION,
        }:
            depth = min(2, HARD_MAX_GRAPH_EXPANSION_DEPTH)
        return AnswerRetrievalPlan(
            mode=RetrievalMode.HYBRID,
            top_k=clamp_top_k(top_k or DEFAULT_TOP_K),
            content_types=content_types,
            canonical_ids=scope.canonical_ids,
            graph_node_ids=scope.graph_node_ids,
            graph_expansion_depth=depth,
            policy_version=self.version,
        )


AnswerRetrievalStrategy = DefaultAnswerRetrievalStrategy
