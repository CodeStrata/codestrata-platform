"""Deterministic portfolio question classification."""

from __future__ import annotations

from codestrata_platform.domain.portfolio_answering.lifecycle import PortfolioQuestionType


class DeterministicPortfolioQuestionClassificationPolicy:
    """Rule-based portfolio question classification (no LLM)."""

    def classify(self, question_text: str) -> PortfolioQuestionType:
        text = question_text.lower()
        if any(token in text for token in ("standardiz", "standard tech", "common stack")):
            return PortfolioQuestionType.TECHNOLOGY_STANDARDIZATION
        if any(token in text for token in ("fragment", "inconsist", "divergent tech")):
            return PortfolioQuestionType.TECHNOLOGY_FRAGMENTATION
        if any(
            token in text
            for token in ("shared exposure", "shared vulnerability", "common exposure")
        ):
            return PortfolioQuestionType.SHARED_EXPOSURE
        if any(token in text for token in ("systemic", "portfolio risk", "hotspot")):
            return PortfolioQuestionType.SYSTEMIC_RISK_EXPLANATION
        if any(
            token in text
            for token in ("cross-repository", "cross repository", "across repositories")
        ):
            return PortfolioQuestionType.CROSS_REPOSITORY_SIGNAL
        if any(token in text for token in ("compare", "comparison", "versus", " vs ")):
            return PortfolioQuestionType.REPOSITORY_COMPARISON
        if any(token in text for token in ("recurring", "repeated finding", "common finding")):
            return PortfolioQuestionType.RECURRING_FINDING_EXPLANATION
        if any(token in text for token in ("modernization", "modernize", "wave", "roadmap")):
            return PortfolioQuestionType.MODERNIZATION_GUIDANCE
        if any(token in text for token in ("overview", "summary", "inventory", "landscape")):
            return PortfolioQuestionType.PORTFOLIO_OVERVIEW
        if "risk" in text:
            return PortfolioQuestionType.SYSTEMIC_RISK_EXPLANATION
        if "finding" in text:
            return PortfolioQuestionType.RECURRING_FINDING_EXPLANATION
        return PortfolioQuestionType.GENERAL_PORTFOLIO_QUESTION


class PortfolioQuestionClassificationService:
    def __init__(
        self,
        policy: DeterministicPortfolioQuestionClassificationPolicy | None = None,
    ) -> None:
        self._policy = policy or DeterministicPortfolioQuestionClassificationPolicy()

    def classify(
        self,
        question_text: str,
        *,
        override: PortfolioQuestionType | None = None,
    ) -> PortfolioQuestionType:
        if override is not None:
            return override
        return self._policy.classify(question_text)
