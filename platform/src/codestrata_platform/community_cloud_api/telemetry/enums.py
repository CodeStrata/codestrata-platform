"""Telemetry enums and bounded vocabularies (Slice 7.7)."""

from __future__ import annotations

from enum import Enum


class TelemetryEventType(str, Enum):
    APPLICATION_STARTED = "application_started"
    APPLICATION_COMPLETED = "application_completed"
    FEATURE_INVOKED = "feature_invoked"
    FEATURE_COMPLETED = "feature_completed"
    OPERATION_FAILED = "operation_failed"


class TelemetryClientName(str, Enum):
    CODESTRATA_CLI = "codestrata_cli"
    VSCODE_EXTENSION = "vscode_extension"
    OTHER_EXTENSION = "other_extension"


class TelemetryOutcome(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNAVAILABLE = "unavailable"


class TelemetryDurationBucket(str, Enum):
    UNDER_1S = "under_1s"
    ONE_TO_5S = "1s_to_5s"
    FIVE_TO_30S = "5s_to_30s"
    THIRTY_TO_2M = "30s_to_2m"
    OVER_2M = "over_2m"
    UNAVAILABLE = "unavailable"


class TelemetryIngestionStatus(str, Enum):
    ACCEPTED = "accepted"
    ALREADY_ACCEPTED = "already_accepted"


class TelemetrySinkStatus(str, Enum):
    ACCEPTED = "accepted"
    UNAVAILABLE = "unavailable"
    REJECTED = "rejected"
