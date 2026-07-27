"""Retrieval taxonomy enums."""

from __future__ import annotations

from enum import StrEnum


class RetrievalContentType(StrEnum):
    REPOSITORY_SUMMARY = "repository_summary"
    TECHNOLOGY = "technology"
    COMPONENT = "component"
    FINDING = "finding"
    RECOMMENDATION = "recommendation"
    METRIC = "metric"
    EVIDENCE = "evidence"
    RISK = "risk"
    CAPABILITY = "capability"
    CONSTRAINT = "constraint"
    OBSERVATION = "observation"
    RELATIONSHIP_SUMMARY = "relationship_summary"
    IMPACT_ANALYSIS = "impact_analysis"
    TRACEABILITY_ANALYSIS = "traceability_analysis"
    COVERAGE_ANALYSIS = "coverage_analysis"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    RISK_ANALYSIS = "risk_analysis"


class RetrievalMode(StrEnum):
    LEXICAL = "lexical"
    VECTOR = "vector"
    HYBRID = "hybrid"
