"""Executive Intelligence lifecycle and taxonomy enums."""

from __future__ import annotations

from enum import StrEnum


class ExecutiveIntelligenceStatus(StrEnum):
    PENDING = "pending"
    AGGREGATING = "aggregating"
    COMPLETED = "completed"
    FAILED = "failed"
    SUPERSEDED = "superseded"


class ExecutiveMetricKey(StrEnum):
    OVERALL_ENGINEERING_HEALTH = "overall_engineering_health"
    PORTFOLIO_RISK = "portfolio_risk"
    MODERNIZATION_READINESS = "modernization_readiness"
    TECHNOLOGY_STANDARDIZATION = "technology_standardization"
    ARCHITECTURE_MATURITY = "architecture_maturity"
    TECHNICAL_DEBT_INDEX = "technical_debt_index"
    SECURITY_POSTURE = "security_posture"
    CLOUD_ADOPTION = "cloud_adoption"
    AI_READINESS = "ai_readiness"
    DOCUMENTATION_COVERAGE = "documentation_coverage"
    ASSESSMENT_COVERAGE = "assessment_coverage"
    REPOSITORY_COVERAGE = "repository_coverage"
    CONFIDENCE = "confidence"
    DEPENDENCY_HEALTH = "dependency_health"


class ExecutiveFindingCategory(StrEnum):
    HIGHEST_RISK_REPOSITORY = "highest_risk_repository"
    MODERNIZATION_CANDIDATE = "modernization_candidate"
    TECHNOLOGY_FRAGMENTATION = "technology_fragmentation"
    DUPLICATED_TECHNOLOGY_STACK = "duplicated_technology_stack"
    UNSUPPORTED_TECHNOLOGY = "unsupported_technology"
    ARCHITECTURE_OUTLIER = "architecture_outlier"
    SECURITY_HOTSPOT = "security_hotspot"
    DEPENDENCY_HOTSPOT = "dependency_hotspot"
    TECHNICAL_DEBT_CONCENTRATION = "technical_debt_concentration"
    PORTFOLIO_STRENGTH = "portfolio_strength"
    PORTFOLIO_WEAKNESS = "portfolio_weakness"


class ExecutiveRecommendationTheme(StrEnum):
    MODERNIZATION = "modernization"
    STANDARDIZATION = "standardization"
    ENGINEERING_INVESTMENT = "engineering_investment"
    ARCHITECTURE_IMPROVEMENT = "architecture_improvement"
    PLATFORM_ENGINEERING = "platform_engineering"
    GOVERNANCE = "governance"
    CLOUD_STRATEGY = "cloud_strategy"
    AI_ADOPTION = "ai_adoption"


class ExecutiveConfidenceBand(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ExecutiveImpactBand(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
