"""Portfolio retrieval content taxonomy."""

from __future__ import annotations

from enum import StrEnum


class PortfolioRetrievalContentType(StrEnum):
    PORTFOLIO_SUMMARY = "portfolio_summary"
    PORTFOLIO_TECHNOLOGY = "portfolio_technology"
    TECHNOLOGY_STANDARDIZATION = "technology_standardization"
    TECHNOLOGY_FRAGMENTATION = "technology_fragmentation"
    PORTFOLIO_FINDING = "portfolio_finding"
    RECURRING_FINDING = "recurring_finding"
    PORTFOLIO_RECOMMENDATION = "portfolio_recommendation"
    RECURRING_RECOMMENDATION = "recurring_recommendation"
    PORTFOLIO_RISK = "portfolio_risk"
    SYSTEMIC_RISK = "systemic_risk"
    MODERNIZATION_THEME = "modernization_theme"
    MODERNIZATION_CANDIDATE = "modernization_candidate"
    MODERNIZATION_WAVE = "modernization_wave"
    PORTFOLIO_COVERAGE = "portfolio_coverage"
    REPOSITORY_PROFILE = "repository_profile"
    REPOSITORY_RISK_PROFILE = "repository_risk_profile"
    REPOSITORY_TECHNOLOGY_PROFILE = "repository_technology_profile"
    CROSS_REPOSITORY_SIGNAL = "cross_repository_signal"
    SHARED_EXPOSURE = "shared_exposure"
    REPOSITORY_SUPPORTING_CONTEXT = "repository_supporting_context"
