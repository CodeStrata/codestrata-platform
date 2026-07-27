"""Portfolio answering taxonomy enums."""

from __future__ import annotations

from enum import StrEnum

# Re-export shared answering lifecycle statuses used by portfolio answers.
from codestrata_platform.domain.answering.lifecycle import (  # noqa: F401
    AnswerConfidenceLevel,
    AnswerStatus,
    ContextSufficiencyStatus,
    GroundingStatus,
)


class PortfolioQuestionType(StrEnum):
    PORTFOLIO_OVERVIEW = "portfolio_overview"
    TECHNOLOGY_STANDARDIZATION = "technology_standardization"
    TECHNOLOGY_FRAGMENTATION = "technology_fragmentation"
    RECURRING_FINDING_EXPLANATION = "recurring_finding_explanation"
    SYSTEMIC_RISK_EXPLANATION = "systemic_risk_explanation"
    CROSS_REPOSITORY_SIGNAL = "cross_repository_signal"
    SHARED_EXPOSURE = "shared_exposure"
    MODERNIZATION_GUIDANCE = "modernization_guidance"
    REPOSITORY_COMPARISON = "repository_comparison"
    GENERAL_PORTFOLIO_QUESTION = "general_portfolio_question"
