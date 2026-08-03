"""Privacy-first CLI event ingestion (Slice 7.9)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.cli_events.catalog import (
    CLI_OPERATION_CATALOG_URN,
    CLI_OPERATION_CATALOG_VERSION,
    CliOperationCatalog,
    default_operation_catalog,
)
from codestrata_platform.community_cloud_api.cli_events.enums import (
    CLI_CLIENT_NAME,
    CLI_EVENT_SOURCE_TYPE,
    CliDurationBucket,
    CliEventIngestionStatus,
    CliEventSinkStatus,
    CliExecutionMode,
    CliFailureCategory,
    CliInvocationSource,
    CliLifecycle,
    CliOutputFormat,
    CliResult,
    CliTerminalEnvironment,
)
from codestrata_platform.community_cloud_api.cli_events.models import (
    CliClient,
    CliEvent,
    CliEventContext,
    CliEventRequest,
)
from codestrata_platform.community_cloud_api.cli_events.policy import (
    COMMUNITY_CLI_EVENT_POLICY_URN,
    COMMUNITY_CLI_EVENT_POLICY_VERSION,
    COMMUNITY_CLI_EVENT_SCHEMA_VERSION,
    CommunityCliEventPolicy,
    default_cli_event_policy,
)
from codestrata_platform.community_cloud_api.cli_events.ports import (
    CliEventSink,
    CliEventSinkResult,
    InMemoryCliEventSink,
    UnavailableCliEventSink,
    ValidatedCliEvent,
)
from codestrata_platform.community_cloud_api.cli_events.responses import CliEventResponse
from codestrata_platform.community_cloud_api.cli_events.routes import (
    CLI_EVENTS_PATH,
    CLI_EVENTS_ROUTE_NAME,
    register_cli_event_routes,
)
from codestrata_platform.community_cloud_api.cli_events.service import IngestCliEvent

__all__ = [
    "CLI_CLIENT_NAME",
    "CLI_EVENT_SOURCE_TYPE",
    "CLI_EVENTS_PATH",
    "CLI_EVENTS_ROUTE_NAME",
    "CLI_OPERATION_CATALOG_URN",
    "CLI_OPERATION_CATALOG_VERSION",
    "COMMUNITY_CLI_EVENT_POLICY_URN",
    "COMMUNITY_CLI_EVENT_POLICY_VERSION",
    "COMMUNITY_CLI_EVENT_SCHEMA_VERSION",
    "CliClient",
    "CliDurationBucket",
    "CliEvent",
    "CliEventContext",
    "CliEventIngestionStatus",
    "CliEventRequest",
    "CliEventResponse",
    "CliEventSink",
    "CliEventSinkResult",
    "CliEventSinkStatus",
    "CliExecutionMode",
    "CliFailureCategory",
    "CliInvocationSource",
    "CliLifecycle",
    "CliOperationCatalog",
    "CliOutputFormat",
    "CliResult",
    "CliTerminalEnvironment",
    "CommunityCliEventPolicy",
    "InMemoryCliEventSink",
    "IngestCliEvent",
    "UnavailableCliEventSink",
    "ValidatedCliEvent",
    "default_cli_event_policy",
    "default_operation_catalog",
    "register_cli_event_routes",
]
