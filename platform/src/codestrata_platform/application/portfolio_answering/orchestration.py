"""Portfolio answer retrieval strategy selection."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.application.portfolio_answering.policies import (
    DEFAULT_TOP_K,
    PORTFOLIO_RETRIEVAL_STRATEGY_VERSION,
    STRATEGY_CONTENT_TYPES,
    clamp_top_k,
)
from codestrata_platform.domain.portfolio_answering.lifecycle import PortfolioQuestionType
from codestrata_platform.domain.portfolio_answering.question import PortfolioQuestionScope
from codestrata_platform.domain.portfolio_retrieval.lifecycle import RepositoryBalanceMode
from codestrata_platform.domain.portfolio_retrieval.taxonomy import PortfolioRetrievalContentType
from codestrata_platform.domain.retrieval.taxonomy import RetrievalMode


@dataclass(frozen=True, slots=True)
class PortfolioAnswerRetrievalPlan:
    mode: RetrievalMode
    top_k: int
    content_types: tuple[PortfolioRetrievalContentType, ...]
    repository_ids: tuple[str, ...]
    repository_balance_mode: RepositoryBalanceMode
    policy_version: str


class DefaultPortfolioAnswerRetrievalStrategy:
    version = PORTFOLIO_RETRIEVAL_STRATEGY_VERSION

    def plan(
        self,
        *,
        question_type: PortfolioQuestionType,
        scope: PortfolioQuestionScope,
        top_k: int | None = None,
    ) -> PortfolioAnswerRetrievalPlan:
        content_types = scope.content_types or STRATEGY_CONTENT_TYPES.get(question_type, ())
        balance = RepositoryBalanceMode.DIVERSIFIED
        if question_type is PortfolioQuestionType.PORTFOLIO_OVERVIEW:
            balance = RepositoryBalanceMode.PROPORTIONAL
        elif question_type is PortfolioQuestionType.SYSTEMIC_RISK_EXPLANATION:
            balance = RepositoryBalanceMode.CRITICALITY_AWARE
        return PortfolioAnswerRetrievalPlan(
            mode=RetrievalMode.HYBRID,
            top_k=clamp_top_k(top_k or DEFAULT_TOP_K),
            content_types=content_types,
            repository_ids=scope.repository_ids,
            repository_balance_mode=balance,
            policy_version=self.version,
        )
