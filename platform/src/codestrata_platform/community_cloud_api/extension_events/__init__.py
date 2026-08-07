"""Privacy-first Extension Event ingestion (Slice 7.10)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.extension_events.catalog import (
    EXTENSION_OPERATION_CATALOG_URN,
    ExtensionOperationCatalog,
    default_operation_catalog,
)
from codestrata_platform.community_cloud_api.extension_events.enums import (
    ACTIVE_EXTENSION_CLIENTS,
    ALLOWED_EXTENSION_CLIENTS,
    CURSOR_EXTENSION_CLIENT,
    EXTENSION_EVENT_SOURCE_TYPE,
    HISTORICAL_EXTENSION_CLIENTS,
    SCHEMA_EXTENSION_CLIENTS,
    ExtensionEventIngestionStatus,
)
from codestrata_platform.community_cloud_api.extension_events.models import (
    ExtensionClient,
    ExtensionEvent,
    ExtensionEventContext,
    ExtensionEventRequest,
)
from codestrata_platform.community_cloud_api.extension_events.policy import (
    COMMUNITY_EXTENSION_EVENT_POLICY_URN,
    COMMUNITY_EXTENSION_EVENT_POLICY_VERSION,
    COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION,
    CommunityExtensionEventPolicy,
    default_extension_event_policy,
)
from codestrata_platform.community_cloud_api.extension_events.ports import (
    ExtensionEventSink,
    InMemoryExtensionEventSink,
    UnavailableExtensionEventSink,
    ValidatedExtensionEvent,
)
from codestrata_platform.community_cloud_api.extension_events.responses import (
    ExtensionEventResponse,
)
from codestrata_platform.community_cloud_api.extension_events.routes import (
    EXTENSION_EVENTS_PATH,
    EXTENSION_EVENTS_ROUTE_NAME,
    register_extension_event_routes,
)
from codestrata_platform.community_cloud_api.extension_events.service import (
    IngestExtensionEvent,
)

__all__ = [
    "ACTIVE_EXTENSION_CLIENTS",
    "ALLOWED_EXTENSION_CLIENTS",
    "COMMUNITY_EXTENSION_EVENT_POLICY_URN",
    "COMMUNITY_EXTENSION_EVENT_POLICY_VERSION",
    "COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION",
    "CURSOR_EXTENSION_CLIENT",
    "EXTENSION_EVENT_SOURCE_TYPE",
    "EXTENSION_EVENTS_PATH",
    "EXTENSION_EVENTS_ROUTE_NAME",
    "EXTENSION_OPERATION_CATALOG_URN",
    "HISTORICAL_EXTENSION_CLIENTS",
    "SCHEMA_EXTENSION_CLIENTS",
    "CommunityExtensionEventPolicy",
    "ExtensionClient",
    "ExtensionEvent",
    "ExtensionEventContext",
    "ExtensionEventIngestionStatus",
    "ExtensionEventRequest",
    "ExtensionEventResponse",
    "ExtensionEventSink",
    "ExtensionOperationCatalog",
    "InMemoryExtensionEventSink",
    "IngestExtensionEvent",
    "UnavailableExtensionEventSink",
    "ValidatedExtensionEvent",
    "default_extension_event_policy",
    "default_operation_catalog",
    "register_extension_event_routes",
]
