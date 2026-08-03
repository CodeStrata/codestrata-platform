"""Assessment metadata enums and bounded vocabularies (Slice 7.8)."""

from __future__ import annotations

from enum import Enum


class AssessmentStatus(str, Enum):
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AssessmentMode(str, Enum):
    DETERMINISTIC = "deterministic"
    DETERMINISTIC_WITH_AI = "deterministic_with_ai"
    UNAVAILABLE = "unavailable"


class AssessmentHead(str, Enum):
    """Canonical executed-head vocabulary (privacy-first Community Cloud)."""

    TECHNOLOGY_INVENTORY = "technology_inventory"
    ARCHITECTURE = "architecture"
    TECHNICAL_DEBT = "technical_debt"
    DEPENDENCY = "dependency"
    SECURITY = "security"
    TESTING = "testing"
    CLOUD_READINESS = "cloud_readiness"
    AI_READINESS = "ai_readiness"
    PERFORMANCE = "performance"
    MODERNIZATION = "modernization"


class RepositoryShape(str, Enum):
    APPLICATION = "application"
    LIBRARY = "library"
    SERVICE = "service"
    CLI = "cli"
    MULTI_MODULE = "multi_module"
    INFRASTRUCTURE = "infrastructure"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class CountBucket(str, Enum):
    NONE = "none"
    ONE_TO_10 = "1_to_10"
    ELEVEN_TO_50 = "11_to_50"
    FIFTY_ONE_TO_200 = "51_to_200"
    TWO_HUNDRED_ONE_TO_1000 = "201_to_1000"
    OVER_1000 = "over_1000"
    UNAVAILABLE = "unavailable"


class AssessmentDurationBucket(str, Enum):
    UNDER_10S = "under_10s"
    TEN_TO_30S = "10s_to_30s"
    THIRTY_TO_2M = "30s_to_2m"
    TWO_TO_10M = "2m_to_10m"
    OVER_10M = "over_10m"
    UNAVAILABLE = "unavailable"


class AssessmentExecutionResult(str, Enum):
    SUCCEEDED = "succeeded"
    PARTIALLY_SUCCEEDED = "partially_succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PrimaryLanguage(str, Enum):
    """Bounded language labels aligned with Engine telemetry categories."""

    PYTHON = "python"
    JAVA = "java"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    CSHARP = "csharp"
    RUST = "rust"
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"


class AssessmentMetadataIngestionStatus(str, Enum):
    ACCEPTED = "accepted"
    ALREADY_ACCEPTED = "already_accepted"


class AssessmentMetadataSinkStatus(str, Enum):
    ACCEPTED = "accepted"
    UNAVAILABLE = "unavailable"
    REJECTED = "rejected"


# Fixed identity event type for this endpoint (not client-supplied).
ASSESSMENT_METADATA_EVENT_TYPE = "assessment_metadata_submitted"
