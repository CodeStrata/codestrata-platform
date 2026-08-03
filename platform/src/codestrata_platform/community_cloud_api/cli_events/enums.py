"""CLI event enums and vocabularies (Slice 7.9)."""

from __future__ import annotations

from enum import Enum


class CliLifecycle(str, Enum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CliResult(str, Enum):
    SUCCEEDED = "succeeded"
    PARTIALLY_SUCCEEDED = "partially_succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNAVAILABLE = "unavailable"


class CliDurationBucket(str, Enum):
    UNDER_1S = "under_1s"
    ONE_TO_5S = "1s_to_5s"
    FIVE_TO_30S = "5s_to_30s"
    THIRTY_TO_2M = "30s_to_2m"
    TWO_TO_10M = "2m_to_10m"
    OVER_10M = "over_10m"
    UNAVAILABLE = "unavailable"


class CliFailureCategory(str, Enum):
    INVALID_CONFIGURATION = "invalid_configuration"
    UNSUPPORTED_REPOSITORY = "unsupported_repository"
    ASSESSMENT_FAILED = "assessment_failed"
    REPORT_GENERATION_FAILED = "report_generation_failed"
    AI_PROVIDER_UNAVAILABLE = "ai_provider_unavailable"
    NETWORK_UNAVAILABLE = "network_unavailable"
    PERMISSION_DENIED = "permission_denied"
    INTERNAL_ERROR = "internal_error"
    CANCELLED = "cancelled"
    UNAVAILABLE = "unavailable"


class CliExecutionMode(str, Enum):
    DETERMINISTIC = "deterministic"
    DETERMINISTIC_WITH_AI = "deterministic_with_ai"
    UNAVAILABLE = "unavailable"


class CliOutputFormat(str, Enum):
    JSON = "json"
    HTML = "html"
    CONSOLE = "console"
    MULTIPLE = "multiple"
    NONE = "none"
    UNAVAILABLE = "unavailable"


class CliInvocationSource(str, Enum):
    TERMINAL = "terminal"
    SCRIPT = "script"
    CI = "ci"
    UNKNOWN = "unknown"


class CliTerminalEnvironment(str, Enum):
    INTERACTIVE = "interactive"
    NON_INTERACTIVE = "non_interactive"
    UNKNOWN = "unknown"


class CliEventIngestionStatus(str, Enum):
    ACCEPTED = "accepted"
    ALREADY_ACCEPTED = "already_accepted"


class CliEventSinkStatus(str, Enum):
    ACCEPTED = "accepted"
    UNAVAILABLE = "unavailable"
    REJECTED = "rejected"


CLI_EVENT_SOURCE_TYPE = "cli_event_submitted"
CLI_CLIENT_NAME = "codestrata_cli"
