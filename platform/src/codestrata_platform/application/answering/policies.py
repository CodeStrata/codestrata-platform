"""Answering policies and configuration helpers."""

from __future__ import annotations

import os

from codestrata_platform.domain.answering.identifiers import (
    AnswerPolicyVersion,
    PromptTemplateVersion,
)
from codestrata_platform.domain.answering.lifecycle import (
    AnswerConfidenceLevel,
    ContextSufficiencyStatus,
    GroundingStatus,
    QuestionType,
)
from codestrata_platform.domain.answering.policy import (
    DEFAULT_MAX_OUTPUT_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_K,
    HARD_MAX_OUTPUT_TOKENS,
    HARD_MAX_TEMPERATURE,
    HARD_MAX_TOP_K,
    AnsweringPolicy,
    GenerationParameters,
)
from codestrata_platform.domain.retrieval.taxonomy import RetrievalContentType

ANSWER_POLICY_VERSION = "1.0.0"
PROMPT_TEMPLATE_VERSION = "1.0.0"
RETRIEVAL_STRATEGY_VERSION = "1.0.0"

ANSWERING_ENABLED_ENV = "CODESTRATA_ANSWERING_ENABLED"
ANSWER_CACHE_ENABLED_ENV = "CODESTRATA_ANSWER_CACHE_ENABLED"
LLM_PROVIDER_ENV = "CODESTRATA_LLM_PROVIDER"
LLM_MODEL_ENV = "CODESTRATA_LLM_MODEL"
LLM_MAX_OUTPUT_TOKENS_ENV = "CODESTRATA_LLM_MAX_OUTPUT_TOKENS"
LLM_TEMPERATURE_ENV = "CODESTRATA_LLM_TEMPERATURE"
LLM_TIMEOUT_SECONDS_ENV = "CODESTRATA_LLM_TIMEOUT_SECONDS"

INJECTION_PHRASES = (
    "ignore previous instructions",
    "reveal system prompt",
    "execute command",
    "send credentials",
    "override safety",
    "call external url",
)


def answering_enabled() -> bool:
    raw = os.environ.get(ANSWERING_ENABLED_ENV, "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def answer_cache_enabled() -> bool:
    raw = os.environ.get(ANSWER_CACHE_ENABLED_ENV, "true").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def configured_llm_provider() -> str:
    return os.environ.get(LLM_PROVIDER_ENV, "deterministic").strip().lower() or "deterministic"


def configured_llm_model() -> str:
    return (
        os.environ.get(LLM_MODEL_ENV, "deterministic-test-answer").strip()
        or "deterministic-test-answer"
    )


def configured_llm_max_output_tokens() -> int:
    raw = os.environ.get(LLM_MAX_OUTPUT_TOKENS_ENV, str(DEFAULT_MAX_OUTPUT_TOKENS)).strip()
    try:
        value = int(raw)
    except ValueError as error:
        raise ValueError("invalid_llm_max_output_tokens") from error
    if value < 1 or value > HARD_MAX_OUTPUT_TOKENS:
        raise ValueError("invalid_llm_max_output_tokens")
    return value


def configured_llm_temperature() -> float:
    raw = os.environ.get(LLM_TEMPERATURE_ENV, str(DEFAULT_TEMPERATURE)).strip()
    try:
        value = float(raw)
    except ValueError as error:
        raise ValueError("invalid_llm_temperature") from error
    if value < 0 or value > HARD_MAX_TEMPERATURE:
        raise ValueError("invalid_llm_temperature")
    return value


def configured_llm_timeout_seconds() -> int:
    raw = os.environ.get(LLM_TIMEOUT_SECONDS_ENV, "30").strip()
    try:
        value = int(raw)
    except ValueError as error:
        raise ValueError("invalid_llm_timeout") from error
    if value < 1 or value > 120:
        raise ValueError("invalid_llm_timeout")
    return value


def default_answering_policy() -> AnsweringPolicy:
    return AnsweringPolicy(
        answer_policy_version=AnswerPolicyVersion(ANSWER_POLICY_VERSION),
        prompt_template_version=PromptTemplateVersion(PROMPT_TEMPLATE_VERSION),
        retrieval_policy_version=RETRIEVAL_STRATEGY_VERSION,
        allow_partially_grounded=True,
        cache_enabled=answer_cache_enabled(),
        generation=GenerationParameters(
            temperature=configured_llm_temperature(),
            max_output_tokens=configured_llm_max_output_tokens(),
            timeout_seconds=configured_llm_timeout_seconds(),
        ),
    )


STRATEGY_CONTENT_TYPES: dict[QuestionType, tuple[RetrievalContentType, ...]] = {
    QuestionType.REPOSITORY_OVERVIEW: (
        RetrievalContentType.REPOSITORY_SUMMARY,
        RetrievalContentType.COVERAGE_ANALYSIS,
        RetrievalContentType.RISK_ANALYSIS,
        RetrievalContentType.DEPENDENCY_ANALYSIS,
        RetrievalContentType.TECHNOLOGY,
    ),
    QuestionType.FINDING_EXPLANATION: (
        RetrievalContentType.FINDING,
        RetrievalContentType.EVIDENCE,
        RetrievalContentType.RECOMMENDATION,
        RetrievalContentType.COMPONENT,
    ),
    QuestionType.RECOMMENDATION_EXPLANATION: (
        RetrievalContentType.RECOMMENDATION,
        RetrievalContentType.FINDING,
        RetrievalContentType.COMPONENT,
    ),
    QuestionType.TECHNOLOGY_IMPACT: (
        RetrievalContentType.TECHNOLOGY,
        RetrievalContentType.COMPONENT,
        RetrievalContentType.FINDING,
        RetrievalContentType.RECOMMENDATION,
        RetrievalContentType.IMPACT_ANALYSIS,
    ),
    QuestionType.COMPONENT_IMPACT: (
        RetrievalContentType.COMPONENT,
        RetrievalContentType.FINDING,
        RetrievalContentType.RECOMMENDATION,
        RetrievalContentType.IMPACT_ANALYSIS,
        RetrievalContentType.TECHNOLOGY,
    ),
    QuestionType.RISK_EXPLANATION: (
        RetrievalContentType.RISK_ANALYSIS,
        RetrievalContentType.FINDING,
        RetrievalContentType.RISK,
        RetrievalContentType.RECOMMENDATION,
    ),
    QuestionType.DEPENDENCY_EXPLANATION: (
        RetrievalContentType.DEPENDENCY_ANALYSIS,
        RetrievalContentType.COMPONENT,
        RetrievalContentType.TECHNOLOGY,
    ),
    QuestionType.TRACEABILITY_EXPLANATION: (
        RetrievalContentType.TRACEABILITY_ANALYSIS,
        RetrievalContentType.FINDING,
        RetrievalContentType.EVIDENCE,
        RetrievalContentType.RECOMMENDATION,
    ),
    QuestionType.MODERNIZATION_GUIDANCE: (
        RetrievalContentType.REPOSITORY_SUMMARY,
        RetrievalContentType.FINDING,
        RetrievalContentType.RECOMMENDATION,
        RetrievalContentType.RISK_ANALYSIS,
        RetrievalContentType.TECHNOLOGY,
    ),
    QuestionType.TECHNOLOGY_EXPLANATION: (
        RetrievalContentType.TECHNOLOGY,
        RetrievalContentType.COMPONENT,
        RetrievalContentType.FINDING,
    ),
    QuestionType.GENERAL_ENGINEERING_QUESTION: (),
}


def clamp_top_k(top_k: int) -> int:
    return max(1, min(top_k, HARD_MAX_TOP_K))


def confidence_from_grounding(
    *,
    sufficiency: ContextSufficiencyStatus,
    grounding: GroundingStatus,
    citation_count: int,
    chunk_count: int,
) -> tuple[AnswerConfidenceLevel, int, tuple[str, ...]]:
    score = 40
    factors: list[str] = []
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
    score = max(0, min(100, score))
    if score >= 75:
        level = AnswerConfidenceLevel.HIGH
    elif score >= 50:
        level = AnswerConfidenceLevel.MEDIUM
    else:
        level = AnswerConfidenceLevel.LOW
    return level, score, tuple(factors)


__all__ = [
    "ANSWER_POLICY_VERSION",
    "DEFAULT_TOP_K",
    "INJECTION_PHRASES",
    "PROMPT_TEMPLATE_VERSION",
    "RETRIEVAL_STRATEGY_VERSION",
    "STRATEGY_CONTENT_TYPES",
    "answer_cache_enabled",
    "answering_enabled",
    "clamp_top_k",
    "confidence_from_grounding",
    "configured_llm_max_output_tokens",
    "configured_llm_model",
    "configured_llm_provider",
    "configured_llm_temperature",
    "configured_llm_timeout_seconds",
    "default_answering_policy",
]
