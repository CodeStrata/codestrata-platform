"""Domain helpers for CEIM severity/category/metric mapping."""

from __future__ import annotations

from codestrata_platform.domain.engineering.enums import (
    EngineeringCategory,
    EngineeringMetricKind,
    EngineeringSeverity,
)
from codestrata_platform.domain.intelligence.enums import (
    FindingCategory,
    FindingSeverity,
    MetricValueKind,
)

_SEVERITY_MAP = {
    FindingSeverity.CRITICAL: EngineeringSeverity.CRITICAL,
    FindingSeverity.HIGH: EngineeringSeverity.HIGH,
    FindingSeverity.MEDIUM: EngineeringSeverity.MEDIUM,
    FindingSeverity.LOW: EngineeringSeverity.LOW,
    FindingSeverity.INFO: EngineeringSeverity.INFO,
}

_CATEGORY_MAP = {
    FindingCategory.SECURITY: EngineeringCategory.SECURITY,
    FindingCategory.PERFORMANCE: EngineeringCategory.PERFORMANCE,
    FindingCategory.ARCHITECTURE: EngineeringCategory.ARCHITECTURE,
    FindingCategory.TESTING: EngineeringCategory.MAINTAINABILITY,
    FindingCategory.DEPENDENCY: EngineeringCategory.DEPENDENCY,
    FindingCategory.MAINTAINABILITY: EngineeringCategory.MAINTAINABILITY,
    FindingCategory.OTHER: EngineeringCategory.OTHER,
}

_METRIC_KIND_MAP = {
    MetricValueKind.INTEGER: EngineeringMetricKind.COUNT,
    MetricValueKind.DECIMAL: EngineeringMetricKind.SCORE,
    MetricValueKind.PERCENTAGE: EngineeringMetricKind.PERCENTAGE,
    MetricValueKind.DURATION: EngineeringMetricKind.DURATION,
    MetricValueKind.COUNT: EngineeringMetricKind.COUNT,
    MetricValueKind.TEXT: EngineeringMetricKind.TEXT,
}

_PRIORITY_SEVERITY = {
    "critical": EngineeringSeverity.CRITICAL,
    "high": EngineeringSeverity.HIGH,
    "medium": EngineeringSeverity.MEDIUM,
    "low": EngineeringSeverity.LOW,
    "info": EngineeringSeverity.INFO,
}


def map_severity(severity: FindingSeverity | str) -> EngineeringSeverity:
    if isinstance(severity, FindingSeverity):
        return _SEVERITY_MAP.get(severity, EngineeringSeverity.UNKNOWN)
    return _PRIORITY_SEVERITY.get(str(severity).strip().lower(), EngineeringSeverity.UNKNOWN)


def map_category(category: FindingCategory | str) -> EngineeringCategory:
    if isinstance(category, FindingCategory):
        return _CATEGORY_MAP.get(category, EngineeringCategory.OTHER)
    raw = str(category).strip().lower().replace(" ", "_").replace("-", "_")
    for item in EngineeringCategory:
        if item.value == raw:
            return item
    aliases = {
        "tech_debt": EngineeringCategory.TECHNICAL_DEBT,
        "technicaldebt": EngineeringCategory.TECHNICAL_DEBT,
        "ai": EngineeringCategory.AI_READINESS,
        "ai_readiness": EngineeringCategory.AI_READINESS,
        "ops": EngineeringCategory.OBSERVABILITY,
    }
    return aliases.get(raw, EngineeringCategory.OTHER)


def map_metric_kind(kind: MetricValueKind | str) -> EngineeringMetricKind:
    if isinstance(kind, MetricValueKind):
        return _METRIC_KIND_MAP.get(kind, EngineeringMetricKind.TEXT)
    raw = str(kind).strip().lower()
    for item in EngineeringMetricKind:
        if item.value == raw:
            return item
    return EngineeringMetricKind.TEXT


def map_priority_to_severity(priority: str) -> EngineeringSeverity:
    return _PRIORITY_SEVERITY.get(priority.strip().lower(), EngineeringSeverity.UNKNOWN)
