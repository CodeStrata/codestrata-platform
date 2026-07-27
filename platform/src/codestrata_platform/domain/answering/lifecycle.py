"""Answering taxonomy and policy enums."""

from __future__ import annotations

from enum import StrEnum


class QuestionType(StrEnum):
    REPOSITORY_OVERVIEW = "repository_overview"
    TECHNOLOGY_EXPLANATION = "technology_explanation"
    FINDING_EXPLANATION = "finding_explanation"
    RECOMMENDATION_EXPLANATION = "recommendation_explanation"
    COMPONENT_IMPACT = "component_impact"
    TECHNOLOGY_IMPACT = "technology_impact"
    RISK_EXPLANATION = "risk_explanation"
    DEPENDENCY_EXPLANATION = "dependency_explanation"
    TRACEABILITY_EXPLANATION = "traceability_explanation"
    MODERNIZATION_GUIDANCE = "modernization_guidance"
    GENERAL_ENGINEERING_QUESTION = "general_engineering_question"


class AnswerStatus(StrEnum):
    PENDING = "pending"
    RETRIEVING = "retrieving"
    CONTEXT_ATTACHED = "context_attached"
    GENERATING = "generating"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class GroundingStatus(StrEnum):
    GROUNDED = "grounded"
    PARTIALLY_GROUNDED = "partially_grounded"
    UNGROUNDED = "ungrounded"
    INSUFFICIENT_CONTEXT = "insufficient_context"


class ContextSufficiencyStatus(StrEnum):
    SUFFICIENT = "sufficient"
    PARTIAL = "partial"
    INSUFFICIENT = "insufficient"


class AnswerConfidenceLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
