"""AI usage enums and vocabularies (Slice 7.11)."""

from __future__ import annotations

from enum import Enum


class AiExecutionMode(str, Enum):
    DETERMINISTIC_WITH_AI = "deterministic_with_ai"
    UNAVAILABLE = "unavailable"


class AiProviderOwnership(str, Enum):
    CUSTOMER_MANAGED = "customer_managed"
    CODESTRATA_MANAGED = "codestrata_managed"
    UNAVAILABLE = "unavailable"


class AiOutcome(str, Enum):
    SUCCEEDED = "succeeded"
    PARTIALLY_SUCCEEDED = "partially_succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNAVAILABLE = "unavailable"


class AiDurationBucket(str, Enum):
    UNDER_1S = "under_1s"
    ONE_TO_5S = "1s_to_5s"
    FIVE_TO_30S = "5s_to_30s"
    THIRTY_TO_2M = "30s_to_2m"
    TWO_TO_10M = "2m_to_10m"
    OVER_10M = "over_10m"
    UNAVAILABLE = "unavailable"


class AiTokenBucket(str, Enum):
    NONE = "none"
    ONE_TO_1K = "1_to_1k"
    ONE_K_TO_4K = "1k_to_4k"
    FOUR_K_TO_16K = "4k_to_16k"
    SIXTEEN_K_TO_64K = "16k_to_64k"
    OVER_64K = "over_64k"
    UNAVAILABLE = "unavailable"


class AiUsageState(str, Enum):
    USED = "used"
    NOT_USED = "not_used"
    UNAVAILABLE = "unavailable"


class AiFailureCategory(str, Enum):
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    AUTHENTICATION_FAILED = "authentication_failed"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    INVALID_CONFIGURATION = "invalid_configuration"
    UNSUPPORTED_MODEL = "unsupported_model"
    CONTEXT_LIMIT_EXCEEDED = "context_limit_exceeded"
    SAFETY_REJECTION = "safety_rejection"
    RESPONSE_INVALID = "response_invalid"
    CANCELLED = "cancelled"
    INTERNAL_ERROR = "internal_error"
    UNAVAILABLE = "unavailable"


class AiInvocationSource(str, Enum):
    CLI = "cli"
    VSCODE_EXTENSION = "vscode_extension"
    CURSOR_EXTENSION = "cursor_extension"
    PLATFORM_SERVICE = "platform_service"
    UNKNOWN = "unknown"


class AiDataScope(str, Enum):
    AGGREGATE_ASSESSMENT_METADATA = "aggregate_assessment_metadata"
    BOUNDED_FINDING_CONTEXT = "bounded_finding_context"
    BOUNDED_RECOMMENDATION_CONTEXT = "bounded_recommendation_context"
    REPOSITORY_CONTEXT = "repository_context"
    UNAVAILABLE = "unavailable"


class AiOutputUsage(str, Enum):
    DISPLAYED_TO_USER = "displayed_to_user"
    INCLUDED_IN_REPORT = "included_in_report"
    INTERNAL_PROCESSING = "internal_processing"
    DISCARDED = "discarded"
    UNAVAILABLE = "unavailable"


class AiUsageIngestionStatus(str, Enum):
    ACCEPTED = "accepted"
    ALREADY_ACCEPTED = "already_accepted"


class AiUsageSinkStatus(str, Enum):
    ACCEPTED = "accepted"
    UNAVAILABLE = "unavailable"
    REJECTED = "rejected"


AI_USAGE_SOURCE_TYPE = "ai_usage_submitted"
ALLOWED_AI_USAGE_CLIENTS: tuple[str, ...] = (
    "codestrata_cli",
    "vscode_extension",
    "cursor_extension",
)

# Ordered ranks for coarse token-bucket consistency (none < ranges < over).
TOKEN_BUCKET_RANK: dict[str, int] = {
    AiTokenBucket.NONE.value: 0,
    AiTokenBucket.ONE_TO_1K.value: 1,
    AiTokenBucket.ONE_K_TO_4K.value: 2,
    AiTokenBucket.FOUR_K_TO_16K.value: 3,
    AiTokenBucket.SIXTEEN_K_TO_64K.value: 4,
    AiTokenBucket.OVER_64K.value: 5,
}
