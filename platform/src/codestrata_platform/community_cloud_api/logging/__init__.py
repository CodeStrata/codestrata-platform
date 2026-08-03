"""Community Cloud API structured logging foundation (Slice 7.5)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.logging.context import (
    LoggingContext,
    SequenceClock,
    SequenceRequestIdFactory,
    create_logging_context,
)
from codestrata_platform.community_cloud_api.logging.formatter import format_log_event
from codestrata_platform.community_cloud_api.logging.logger import (
    CommunityCloudLogger,
    MemoryLogSink,
    NullLogSink,
    default_community_cloud_logger,
)
from codestrata_platform.community_cloud_api.logging.middleware import (
    asgi_client_host,
    begin_request_logging,
    finish_request_logging,
)
from codestrata_platform.community_cloud_api.logging.models import (
    COMMUNITY_LOGGING_POLICY_URN,
    COMMUNITY_LOGGING_POLICY_VERSION,
    CommunityLoggingPolicy,
    LogEventType,
    LogLevel,
    LoggingDiagnostic,
    StructuredLogEvent,
)
from codestrata_platform.community_cloud_api.logging.policy import (
    ACTIVE_COMMUNITY_LOGGING_POLICY,
    default_logging_policy,
)

__all__ = [
    "ACTIVE_COMMUNITY_LOGGING_POLICY",
    "COMMUNITY_LOGGING_POLICY_URN",
    "COMMUNITY_LOGGING_POLICY_VERSION",
    "CommunityCloudLogger",
    "CommunityLoggingPolicy",
    "LogEventType",
    "LogLevel",
    "LoggingContext",
    "LoggingDiagnostic",
    "MemoryLogSink",
    "NullLogSink",
    "SequenceClock",
    "SequenceRequestIdFactory",
    "StructuredLogEvent",
    "asgi_client_host",
    "begin_request_logging",
    "create_logging_context",
    "default_community_cloud_logger",
    "default_logging_policy",
    "finish_request_logging",
    "format_log_event",
]
