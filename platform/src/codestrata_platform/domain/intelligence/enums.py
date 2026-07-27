"""Assessment intelligence enums."""

from __future__ import annotations

from enum import StrEnum


class FindingCategory(StrEnum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    DEPENDENCY = "dependency"
    MAINTAINABILITY = "maintainability"
    OTHER = "other"


class FindingSeverity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class RecommendationPriority(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DEFERRED = "deferred"


class IntelligenceIngestionStatus(StrEnum):
    PENDING = "pending"
    INGESTING = "ingesting"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class MetricValueKind(StrEnum):
    INTEGER = "integer"
    DECIMAL = "decimal"
    PERCENTAGE = "percentage"
    DURATION = "duration"
    COUNT = "count"
    TEXT = "text"
