"""Portfolio retrieval policies and configuration helpers.

Embedding configuration falls back to the shared Engineering Retrieval
environment variables (``CODESTRATA_EMBEDDING_*``) whenever the
portfolio-specific overrides (``CODESTRATA_PORTFOLIO_EMBEDDING_*``) are not
set, so a single embedding provider can serve both retrieval domains by
default.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from codestrata_platform.application.retrieval.policies import (
    configured_embedding_dimension as _shared_embedding_dimension,
)
from codestrata_platform.application.retrieval.policies import (
    configured_embedding_model as _shared_embedding_model,
)
from codestrata_platform.application.retrieval.policies import (
    configured_embedding_provider as _shared_embedding_provider,
)
from codestrata_platform.domain.portfolio.lifecycle import RepositoryCriticality
from codestrata_platform.domain.portfolio_retrieval.lifecycle import RepositoryBalanceMode
from codestrata_platform.domain.portfolio_retrieval.query import PortfolioRetrievalScore

PORTFOLIO_RETRIEVAL_SCHEMA_VERSION = "1.0"
PORTFOLIO_CHUNKING_POLICY_VERSION = "1.0.0"
PORTFOLIO_RANKING_POLICY_VERSION = "1.0.0"
PORTFOLIO_CONTEXT_POLICY_VERSION = "1.0.0"

PORTFOLIO_RETRIEVAL_ENABLED_ENV = "CODESTRATA_PORTFOLIO_RETRIEVAL_ENABLED"
PORTFOLIO_EMBEDDING_PROVIDER_ENV = "CODESTRATA_PORTFOLIO_EMBEDDING_PROVIDER"
PORTFOLIO_EMBEDDING_MODEL_ENV = "CODESTRATA_PORTFOLIO_EMBEDDING_MODEL"
PORTFOLIO_EMBEDDING_DIMENSION_ENV = "CODESTRATA_PORTFOLIO_EMBEDDING_DIMENSION"

DEFAULT_PORTFOLIO_CONTEXT_MAX_TOKENS = 10_000
HARD_PORTFOLIO_CONTEXT_MAX_TOKENS = 20_000
DEFAULT_PORTFOLIO_CONTEXT_MAX_REPOSITORIES = 20
HARD_PORTFOLIO_CONTEXT_MAX_REPOSITORIES = 100


def portfolio_retrieval_enabled() -> bool:
    raw = os.environ.get(PORTFOLIO_RETRIEVAL_ENABLED_ENV, "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def configured_portfolio_embedding_provider() -> str:
    raw = os.environ.get(PORTFOLIO_EMBEDDING_PROVIDER_ENV, "").strip().lower()
    return raw or _shared_embedding_provider()


def configured_portfolio_embedding_model() -> str:
    raw = os.environ.get(PORTFOLIO_EMBEDDING_MODEL_ENV, "").strip()
    return raw or _shared_embedding_model()


def configured_portfolio_embedding_dimension() -> int:
    raw = os.environ.get(PORTFOLIO_EMBEDDING_DIMENSION_ENV, "").strip()
    if not raw:
        return _shared_embedding_dimension()
    try:
        return int(raw)
    except ValueError as error:
        raise ValueError("invalid_portfolio_embedding_dimension") from error


class DefaultPortfolioChunkingPolicy:
    """Deterministic chunk sizing bounds for portfolio retrieval documents."""

    version = PORTFOLIO_CHUNKING_POLICY_VERSION
    target_min_tokens = 350
    target_max_tokens = 700
    hard_max_tokens = 1000


@dataclass(frozen=True, slots=True)
class DefaultPortfolioHybridRetrievalPolicy:
    """Explicit hybrid scoring weights for portfolio-scoped retrieval.

    Weights are chosen to sum to ``1.0`` so ``final_score`` (before any
    repository-balance adjustment) stays within a comparable ``[0, 1]`` range
    across queries:

    - ``lexical_weight``        0.20 - keyword/phrase overlap
    - ``vector_weight``         0.30 - semantic similarity
    - ``portfolio_weight``      0.20 - portfolio-level aggregate relevance
      (e.g. recurring findings/recommendations, systemic risk)
    - ``repository_weight``     0.10 - repository-scoped relevance/coverage
    - ``systemic_weight``       0.10 - cross-repository/systemic signal
    - ``source_quality_weight`` 0.05 - evidence/coverage completeness
    - ``freshness_weight``      0.05 - assessment recency
    """

    version: str = PORTFOLIO_RANKING_POLICY_VERSION
    lexical_weight: float = 0.20
    vector_weight: float = 0.30
    portfolio_weight: float = 0.20
    repository_weight: float = 0.10
    systemic_weight: float = 0.10
    source_quality_weight: float = 0.05
    freshness_weight: float = 0.05

    def combine(
        self,
        *,
        lexical_score: float = 0.0,
        vector_score: float = 0.0,
        portfolio_score: float = 0.0,
        repository_score: float = 0.0,
        systemic_score: float = 0.0,
        source_quality_score: float = 0.0,
        freshness_score: float = 0.0,
        balance_adjustment: float = 0.0,
    ) -> PortfolioRetrievalScore:
        weighted = (
            self.lexical_weight * lexical_score
            + self.vector_weight * vector_score
            + self.portfolio_weight * portfolio_score
            + self.repository_weight * repository_score
            + self.systemic_weight * systemic_score
            + self.source_quality_weight * source_quality_score
            + self.freshness_weight * freshness_score
        )
        final = max(0.0, weighted + balance_adjustment)
        return PortfolioRetrievalScore(
            lexical_score=round(lexical_score, 6),
            vector_score=round(vector_score, 6),
            portfolio_score=round(portfolio_score, 6),
            repository_score=round(repository_score, 6),
            systemic_score=round(systemic_score, 6),
            source_quality_score=round(source_quality_score, 6),
            freshness_score=round(freshness_score, 6),
            balance_adjustment=round(balance_adjustment, 6),
            final_score=round(final, 6),
            ranking_policy_version=self.version,
        )


@dataclass(frozen=True, slots=True)
class DefaultRepositoryBalancePolicy:
    """Deterministic repository-balance adjustments applied during ranking.

    - ``NONE``: no adjustment.
    - ``DIVERSIFIED``: penalize each additional hit contributed by a
      repository that has already appeared earlier in the ranked list, so
      results spread across more repositories.
    - ``CRITICALITY_AWARE``: boost hits whose primary repository is of
      higher declared criticality and mildly penalize unspecified/low
      criticality repositories.
    """

    version: str = PORTFOLIO_RANKING_POLICY_VERSION
    diversification_penalty_per_repeat: float = 0.08
    max_diversification_penalty: float = 0.4
    criticality_adjustments: dict[RepositoryCriticality, float] = field(
        default_factory=lambda: {
            RepositoryCriticality.MISSION_CRITICAL: 0.08,
            RepositoryCriticality.HIGH: 0.04,
            RepositoryCriticality.MEDIUM: 0.0,
            RepositoryCriticality.LOW: -0.02,
            RepositoryCriticality.UNSPECIFIED: 0.0,
        }
    )

    def diversification_adjustment(self, *, prior_occurrences: int) -> float:
        penalty = min(
            self.max_diversification_penalty,
            self.diversification_penalty_per_repeat * prior_occurrences,
        )
        return -penalty

    def criticality_adjustment(self, criticality: RepositoryCriticality) -> float:
        return self.criticality_adjustments.get(criticality, 0.0)


@dataclass(frozen=True, slots=True)
class DefaultPortfolioContextPolicy:
    """Bounded context-assembly limits for portfolio retrieval."""

    version: str = PORTFOLIO_CONTEXT_POLICY_VERSION
    default_max_tokens: int = DEFAULT_PORTFOLIO_CONTEXT_MAX_TOKENS
    hard_max_tokens: int = HARD_PORTFOLIO_CONTEXT_MAX_TOKENS
    default_max_repositories: int = DEFAULT_PORTFOLIO_CONTEXT_MAX_REPOSITORIES
    hard_max_repositories: int = HARD_PORTFOLIO_CONTEXT_MAX_REPOSITORIES


__all__ = [
    "DEFAULT_PORTFOLIO_CONTEXT_MAX_REPOSITORIES",
    "DEFAULT_PORTFOLIO_CONTEXT_MAX_TOKENS",
    "HARD_PORTFOLIO_CONTEXT_MAX_REPOSITORIES",
    "HARD_PORTFOLIO_CONTEXT_MAX_TOKENS",
    "PORTFOLIO_CHUNKING_POLICY_VERSION",
    "PORTFOLIO_CONTEXT_POLICY_VERSION",
    "PORTFOLIO_RANKING_POLICY_VERSION",
    "PORTFOLIO_RETRIEVAL_SCHEMA_VERSION",
    "DefaultPortfolioChunkingPolicy",
    "DefaultPortfolioContextPolicy",
    "DefaultPortfolioHybridRetrievalPolicy",
    "DefaultRepositoryBalancePolicy",
    "RepositoryBalanceMode",
    "configured_portfolio_embedding_dimension",
    "configured_portfolio_embedding_model",
    "configured_portfolio_embedding_provider",
    "portfolio_retrieval_enabled",
]
