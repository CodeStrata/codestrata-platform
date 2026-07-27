"""Deterministic repository-balance ranking adjustments."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from codestrata_platform.application.portfolio_retrieval.policies import (
    DefaultRepositoryBalancePolicy,
)
from codestrata_platform.domain.portfolio.lifecycle import RepositoryCriticality
from codestrata_platform.domain.portfolio_retrieval.lifecycle import RepositoryBalanceMode
from codestrata_platform.domain.portfolio_retrieval.result import PortfolioRetrievalHit


def apply_repository_balance(
    hits: tuple[PortfolioRetrievalHit, ...],
    mode: RepositoryBalanceMode,
    criticality_lookup: Mapping[str, RepositoryCriticality] | None = None,
    *,
    policy: DefaultRepositoryBalancePolicy | None = None,
) -> tuple[PortfolioRetrievalHit, ...]:
    """Apply a deterministic repository-balance adjustment to ranked hits.

    Hits are expected to already be ranked by ``score.final_score``
    descending; this re-scores each hit's ``balance_adjustment`` in that
    order and re-sorts the result stably by the adjusted final score.
    """

    if mode is RepositoryBalanceMode.NONE or not hits:
        return hits

    active_policy = policy or DefaultRepositoryBalancePolicy()
    lookup = criticality_lookup or {}
    repository_occurrences: dict[str, int] = {}
    adjusted: list[PortfolioRetrievalHit] = []

    for hit in hits:
        repository_key = hit.primary_repository_id.value if hit.primary_repository_id else None
        adjustment = 0.0

        if mode is RepositoryBalanceMode.DIVERSIFIED and repository_key is not None:
            prior_occurrences = repository_occurrences.get(repository_key, 0)
            adjustment = active_policy.diversification_adjustment(
                prior_occurrences=prior_occurrences
            )
        elif mode is RepositoryBalanceMode.CRITICALITY_AWARE:
            criticality = (
                lookup.get(repository_key, RepositoryCriticality.UNSPECIFIED)
                if repository_key is not None
                else RepositoryCriticality.UNSPECIFIED
            )
            adjustment = active_policy.criticality_adjustment(criticality)

        if repository_key is not None:
            repository_occurrences[repository_key] = (
                repository_occurrences.get(repository_key, 0) + 1
            )

        base_final = hit.score.final_score - hit.score.balance_adjustment
        new_balance_adjustment = hit.score.balance_adjustment + adjustment
        new_final_score = max(0.0, base_final + new_balance_adjustment)
        new_score = replace(
            hit.score,
            balance_adjustment=round(new_balance_adjustment, 6),
            final_score=round(new_final_score, 6),
        )
        adjusted.append(replace(hit, score=new_score))

    return tuple(sorted(adjusted, key=lambda item: -item.score.final_score))


__all__ = ["apply_repository_balance"]
