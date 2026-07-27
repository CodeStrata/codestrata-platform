"""Canonical engineering enums shared across Platform consumers."""

from __future__ import annotations

from enum import StrEnum


class EngineeringSeverity(StrEnum):
    UNKNOWN = "unknown"
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EngineeringCategory(StrEnum):
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    CLOUD = "cloud"
    DEPENDENCY = "dependency"
    TECHNICAL_DEBT = "technical_debt"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"
    DOCUMENTATION = "documentation"
    MAINTAINABILITY = "maintainability"
    AI_READINESS = "ai_readiness"
    OBSERVABILITY = "observability"
    COST = "cost"
    OTHER = "other"


class EngineeringSnapshotStatus(StrEnum):
    DRAFT = "draft"
    BUILDING = "building"
    PUBLISHED = "published"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class EngineeringRelationshipType(StrEnum):
    USES = "uses"
    HAS = "has"
    SUPPORTED_BY = "supported_by"
    RESOLVES = "resolves"
    PART_OF = "part_of"
    DEPENDS_ON = "depends_on"
    RELATED_TO = "related_to"
    TAGS = "tags"


class EngineeringMetricKind(StrEnum):
    SCORE = "score"
    COUNT = "count"
    RATIO = "ratio"
    DURATION = "duration"
    PERCENTAGE = "percentage"
    COMPLEXITY = "complexity"
    COVERAGE = "coverage"
    TREND = "trend"
    TEXT = "text"


class EvidenceKind(StrEnum):
    FILE = "file"
    DIRECTORY = "directory"
    MODULE = "module"
    NAMESPACE = "namespace"
    PACKAGE = "package"
    TYPE = "type"
    METHOD = "method"
    CONFIGURATION = "configuration"
    DATABASE_OBJECT = "database_object"
    CONTAINER = "container"
    API = "api"
    QUEUE = "queue"
    CLOUD_RESOURCE = "cloud_resource"
    OTHER = "other"
