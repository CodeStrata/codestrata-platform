"""Portfolio answering policies and configuration helpers."""

from __future__ import annotations

import os

from codestrata_platform.application.answering.policies import (
    INJECTION_PHRASES,
    configured_llm_max_output_tokens,
    configured_llm_model,
    configured_llm_provider,
    configured_llm_temperature,
    configured_llm_timeout_seconds,
)
from codestrata_platform.domain.answering.identifiers import (
    AnswerPolicyVersion,
    PromptTemplateVersion,
)
from codestrata_platform.domain.answering.lifecycle import (
    AnswerConfidenceLevel,
    ContextSufficiencyStatus,
    GroundingStatus,
)
from codestrata_platform.domain.answering.policy import (
    DEFAULT_TOP_K,
    HARD_MAX_TOP_K,
    AnsweringPolicy,
    GenerationParameters,
)
from codestrata_platform.domain.portfolio_answering.lifecycle import PortfolioQuestionType
from codestrata_platform.domain.portfolio_retrieval.taxonomy import PortfolioRetrievalContentType

PORTFOLIO_ANSWER_POLICY_VERSION = "1.0.0"
PORTFOLIO_PROMPT_TEMPLATE_VERSION = "1.0.0"
PORTFOLIO_RETRIEVAL_STRATEGY_VERSION = "1.0.0"

PORTFOLIO_ANSWERING_ENABLED_ENV = "CODESTRATA_PORTFOLIO_ANSWERING_ENABLED"
PORTFOLIO_ANSWER_CACHE_ENABLED_ENV = "CODESTRATA_PORTFOLIO_ANSWER_CACHE_ENABLED"


def portfolio_answering_enabled() -> bool:
    raw = os.environ.get(PORTFOLIO_ANSWERING_ENABLED_ENV, "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def portfolio_answer_cache_enabled() -> bool:
    raw = os.environ.get(PORTFOLIO_ANSWER_CACHE_ENABLED_ENV, "true").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def default_portfolio_answering_policy() -> AnsweringPolicy:
    return AnsweringPolicy(
        answer_policy_version=AnswerPolicyVersion(PORTFOLIO_ANSWER_POLICY_VERSION),
        prompt_template_version=PromptTemplateVersion(PORTFOLIO_PROMPT_TEMPLATE_VERSION),
        retrieval_policy_version=PORTFOLIO_RETRIEVAL_STRATEGY_VERSION,
        allow_partially_grounded=True,
        cache_enabled=portfolio_answer_cache_enabled(),
        generation=GenerationParameters(
            temperature=configured_llm_temperature(),
            max_output_tokens=configured_llm_max_output_tokens(),
            timeout_seconds=configured_llm_timeout_seconds(),
        ),
    )


STRATEGY_CONTENT_TYPES: dict[
    PortfolioQuestionType, tuple[PortfolioRetrievalContentType, ...]
] = {
    PortfolioQuestionType.PORTFOLIO_OVERVIEW: (
        PortfolioRetrievalContentType.PORTFOLIO_SUMMARY,
        PortfolioRetrievalContentType.PORTFOLIO_COVERAGE,
        PortfolioRetrievalContentType.SYSTEMIC_RISK,
        PortfolioRetrievalContentType.PORTFOLIO_TECHNOLOGY,
        PortfolioRetrievalContentType.REPOSITORY_PROFILE,
    ),
    PortfolioQuestionType.TECHNOLOGY_STANDARDIZATION: (
        PortfolioRetrievalContentType.TECHNOLOGY_STANDARDIZATION,
        PortfolioRetrievalContentType.PORTFOLIO_TECHNOLOGY,
        PortfolioRetrievalContentType.REPOSITORY_TECHNOLOGY_PROFILE,
    ),
    PortfolioQuestionType.TECHNOLOGY_FRAGMENTATION: (
        PortfolioRetrievalContentType.TECHNOLOGY_FRAGMENTATION,
        PortfolioRetrievalContentType.PORTFOLIO_TECHNOLOGY,
        PortfolioRetrievalContentType.REPOSITORY_TECHNOLOGY_PROFILE,
    ),
    PortfolioQuestionType.RECURRING_FINDING_EXPLANATION: (
        PortfolioRetrievalContentType.RECURRING_FINDING,
        PortfolioRetrievalContentType.PORTFOLIO_FINDING,
        PortfolioRetrievalContentType.RECURRING_RECOMMENDATION,
        PortfolioRetrievalContentType.REPOSITORY_SUPPORTING_CONTEXT,
    ),
    PortfolioQuestionType.SYSTEMIC_RISK_EXPLANATION: (
        PortfolioRetrievalContentType.SYSTEMIC_RISK,
        PortfolioRetrievalContentType.PORTFOLIO_RISK,
        PortfolioRetrievalContentType.SHARED_EXPOSURE,
        PortfolioRetrievalContentType.REPOSITORY_RISK_PROFILE,
    ),
    PortfolioQuestionType.CROSS_REPOSITORY_SIGNAL: (
        PortfolioRetrievalContentType.CROSS_REPOSITORY_SIGNAL,
        PortfolioRetrievalContentType.SHARED_EXPOSURE,
        PortfolioRetrievalContentType.REPOSITORY_PROFILE,
    ),
    PortfolioQuestionType.SHARED_EXPOSURE: (
        PortfolioRetrievalContentType.SHARED_EXPOSURE,
        PortfolioRetrievalContentType.CROSS_REPOSITORY_SIGNAL,
        PortfolioRetrievalContentType.SYSTEMIC_RISK,
    ),
    PortfolioQuestionType.MODERNIZATION_GUIDANCE: (
        PortfolioRetrievalContentType.MODERNIZATION_CANDIDATE,
        PortfolioRetrievalContentType.MODERNIZATION_WAVE,
        PortfolioRetrievalContentType.MODERNIZATION_THEME,
        PortfolioRetrievalContentType.PORTFOLIO_SUMMARY,
        PortfolioRetrievalContentType.SYSTEMIC_RISK,
    ),
    PortfolioQuestionType.REPOSITORY_COMPARISON: (
        PortfolioRetrievalContentType.REPOSITORY_PROFILE,
        PortfolioRetrievalContentType.REPOSITORY_RISK_PROFILE,
        PortfolioRetrievalContentType.REPOSITORY_TECHNOLOGY_PROFILE,
        PortfolioRetrievalContentType.REPOSITORY_SUPPORTING_CONTEXT,
    ),
    PortfolioQuestionType.GENERAL_PORTFOLIO_QUESTION: (),
}


def clamp_top_k(top_k: int) -> int:
    return max(1, min(top_k, HARD_MAX_TOP_K))


def confidence_from_grounding(
    *,
    sufficiency: ContextSufficiencyStatus,
    grounding: GroundingStatus,
    citation_count: int,
    chunk_count: int,
    repository_count: int,
    diagnostic_kinds: tuple[str, ...] = (),
) -> tuple[AnswerConfidenceLevel, int, tuple[str, ...]]:
    score = 40
    factors: list[str] = []
    kinds = set(diagnostic_kinds)
    if sufficiency is ContextSufficiencyStatus.SUFFICIENT:
        score += 25
        factors.append("sufficient_context")
    elif sufficiency is ContextSufficiencyStatus.PARTIAL:
        score += 10
        factors.append("partial_context")
    else:
        factors.append("insufficient_context")
    if grounding is GroundingStatus.GROUNDED:
        score += 25
        factors.append("grounded")
    elif grounding is GroundingStatus.PARTIALLY_GROUNDED:
        score += 10
        factors.append("partially_grounded")
    else:
        factors.append(grounding.value)
    if citation_count >= 2:
        score += 5
        factors.append("multiple_citations")
    if chunk_count >= 3:
        score += 5
        factors.append("diverse_chunks")
    if repository_count >= 2:
        score += 5
        factors.append("cross_repository_context")
    if "unavailable_repository" in kinds:
        score -= 10
        factors.append("unavailable_repositories")
    if "stale_repository" in kinds:
        score -= 5
        factors.append("stale_repositories")
    if "excluded_repository" in kinds:
        score -= 5
        factors.append("excluded_repositories")
    if "truncated" in kinds:
        score -= 5
        factors.append("context_truncated")
    score = max(0, min(100, score))
    # Low-evidence answers cannot receive high confidence.
    if grounding is not GroundingStatus.GROUNDED:
        score = min(score, 74)
    if sufficiency is ContextSufficiencyStatus.INSUFFICIENT:
        score = min(score, 40)
    if citation_count < 1 and grounding is not GroundingStatus.INSUFFICIENT_CONTEXT:
        score = min(score, 60)
    if score >= 75:
        level = AnswerConfidenceLevel.HIGH
    elif score >= 50:
        level = AnswerConfidenceLevel.MEDIUM
    else:
        level = AnswerConfidenceLevel.LOW
    return level, score, tuple(factors)


__all__ = [
    "DEFAULT_TOP_K",
    "INJECTION_PHRASES",
    "PORTFOLIO_ANSWER_POLICY_VERSION",
    "PORTFOLIO_PROMPT_TEMPLATE_VERSION",
    "PORTFOLIO_RETRIEVAL_STRATEGY_VERSION",
    "STRATEGY_CONTENT_TYPES",
    "clamp_top_k",
    "confidence_from_grounding",
    "configured_llm_model",
    "configured_llm_provider",
    "default_portfolio_answering_policy",
    "portfolio_answer_cache_enabled",
    "portfolio_answering_enabled",
]
