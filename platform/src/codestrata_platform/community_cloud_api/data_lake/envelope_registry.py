"""Static registry binding each :class:`~.enums.EventStream` to its source contract (Slice 8.3).

This is the single lookup table every envelope builder consults to resolve:
the endpoint request model, the allowlisted payload projector, the client
type extractor, and the source schema/policy identity for one event stream.
Building the registry does not import anything from ``routes.py``/
``service.py`` in any endpoint package — only ``models.py``, ``enums.py``,
and ``policy.py`` — so this module carries no HTTP-wiring dependency.
"""

from __future__ import annotations

from codestrata_platform.community_cloud_api.ai_usage.enums import ALLOWED_AI_USAGE_CLIENTS
from codestrata_platform.community_cloud_api.ai_usage.models import AiUsageRequest
from codestrata_platform.community_cloud_api.ai_usage.policy import (
    COMMUNITY_AI_USAGE_POLICY_URN,
    COMMUNITY_AI_USAGE_SCHEMA_VERSION,
    default_ai_usage_policy,
)
from codestrata_platform.community_cloud_api.assessment_metadata.models import (
    AssessmentMetadataRequest,
)
from codestrata_platform.community_cloud_api.assessment_metadata.policy import (
    COMMUNITY_ASSESSMENT_METADATA_POLICY_URN,
    COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION,
    COMMUNITY_ASSESSMENT_METADATA_SUPPORTED_SCHEMA_VERSIONS,
)
from codestrata_platform.community_cloud_api.cli_events.enums import CLI_CLIENT_NAME
from codestrata_platform.community_cloud_api.cli_events.models import CliEventRequest
from codestrata_platform.community_cloud_api.cli_events.policy import (
    COMMUNITY_CLI_EVENT_POLICY_URN,
    COMMUNITY_CLI_EVENT_SCHEMA_VERSION,
    default_cli_event_policy,
)
from codestrata_platform.community_cloud_api.data_lake.enums import EventStream
from codestrata_platform.community_cloud_api.data_lake.source_contracts import (
    SourceContractDescriptor,
    SourceContractError,
)
from codestrata_platform.community_cloud_api.data_lake.streams import (
    ai_usage as ai_usage_stream,
)
from codestrata_platform.community_cloud_api.data_lake.streams import (
    assessment_metadata as assessment_metadata_stream,
)
from codestrata_platform.community_cloud_api.data_lake.streams import (
    cli_events as cli_events_stream,
)
from codestrata_platform.community_cloud_api.data_lake.streams import (
    extension_events as extension_events_stream,
)
from codestrata_platform.community_cloud_api.data_lake.streams import (
    telemetry as telemetry_stream,
)
from codestrata_platform.community_cloud_api.extension_events.enums import (
    ALLOWED_EXTENSION_CLIENTS,
)
from codestrata_platform.community_cloud_api.extension_events.models import (
    ExtensionEventRequest,
)
from codestrata_platform.community_cloud_api.extension_events.policy import (
    COMMUNITY_EXTENSION_EVENT_POLICY_URN,
    COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION,
    default_extension_event_policy,
)
from codestrata_platform.community_cloud_api.telemetry.enums import TelemetryClientName
from codestrata_platform.community_cloud_api.telemetry.models import TelemetryIngestionRequest
from codestrata_platform.community_cloud_api.telemetry.policy import (
    COMMUNITY_TELEMETRY_POLICY_URN,
    COMMUNITY_TELEMETRY_SCHEMA_VERSION,
)


class UnknownEventStreamError(SourceContractError):
    """Raised when a stream has no registered source contract."""


_TELEMETRY_ALLOWED_CLIENTS = frozenset(item.value for item in TelemetryClientName)

_REGISTRY: dict[EventStream, SourceContractDescriptor] = {
    EventStream.TELEMETRY: SourceContractDescriptor(
        event_stream=EventStream.TELEMETRY,
        schema_name=telemetry_stream.SCHEMA_NAME,
        schema_version=COMMUNITY_TELEMETRY_SCHEMA_VERSION,
        policy_id=COMMUNITY_TELEMETRY_POLICY_URN,
        request_model=TelemetryIngestionRequest,
        allowed_client_types=_TELEMETRY_ALLOWED_CLIENTS,
        project_payload=telemetry_stream.project_payload,
        client_type_extractor=telemetry_stream.client_type_from_request,
    ),
    EventStream.ASSESSMENT_METADATA: SourceContractDescriptor(
        event_stream=EventStream.ASSESSMENT_METADATA,
        schema_name=assessment_metadata_stream.SCHEMA_NAME,
        schema_version=COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION,
        policy_id=COMMUNITY_ASSESSMENT_METADATA_POLICY_URN,
        request_model=AssessmentMetadataRequest,
        allowed_client_types=_TELEMETRY_ALLOWED_CLIENTS,
        project_payload=assessment_metadata_stream.project_payload,
        client_type_extractor=assessment_metadata_stream.client_type_from_request,
        supported_schema_versions=COMMUNITY_ASSESSMENT_METADATA_SUPPORTED_SCHEMA_VERSIONS,
    ),
    EventStream.CLI_EVENT: SourceContractDescriptor(
        event_stream=EventStream.CLI_EVENT,
        schema_name=cli_events_stream.SCHEMA_NAME,
        schema_version=COMMUNITY_CLI_EVENT_SCHEMA_VERSION,
        policy_id=COMMUNITY_CLI_EVENT_POLICY_URN,
        request_model=CliEventRequest,
        allowed_client_types=frozenset({CLI_CLIENT_NAME}),
        project_payload=cli_events_stream.project_payload,
        client_type_extractor=cli_events_stream.client_type_from_request,
        catalog_versions={
            "operation_catalog_version": default_cli_event_policy().operation_catalog_version,
        },
    ),
    EventStream.EXTENSION_EVENT: SourceContractDescriptor(
        event_stream=EventStream.EXTENSION_EVENT,
        schema_name=extension_events_stream.SCHEMA_NAME,
        schema_version=COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION,
        policy_id=COMMUNITY_EXTENSION_EVENT_POLICY_URN,
        request_model=ExtensionEventRequest,
        allowed_client_types=frozenset(ALLOWED_EXTENSION_CLIENTS),
        project_payload=extension_events_stream.project_payload,
        client_type_extractor=extension_events_stream.client_type_from_request,
        catalog_versions={
            "operation_catalog_version": default_extension_event_policy().operation_catalog_version,
        },
    ),
    EventStream.AI_USAGE: SourceContractDescriptor(
        event_stream=EventStream.AI_USAGE,
        schema_name=ai_usage_stream.SCHEMA_NAME,
        schema_version=COMMUNITY_AI_USAGE_SCHEMA_VERSION,
        policy_id=COMMUNITY_AI_USAGE_POLICY_URN,
        request_model=AiUsageRequest,
        allowed_client_types=frozenset(ALLOWED_AI_USAGE_CLIENTS),
        project_payload=ai_usage_stream.project_payload,
        client_type_extractor=ai_usage_stream.client_type_from_request,
        catalog_versions={
            "capability_catalog_version": default_ai_usage_policy().capability_catalog_version,
            "model_catalog_version": default_ai_usage_policy().model_catalog_version,
            "provider_catalog_version": default_ai_usage_policy().provider_catalog_version,
        },
    ),
}


def get_source_contract(event_stream: EventStream | str) -> SourceContractDescriptor:
    """Look up the registered source contract for ``event_stream``.

    Raises :class:`UnknownEventStreamError` for any stream not registered —
    fail-closed, never a partial or best-effort match.
    """

    if isinstance(event_stream, EventStream):
        key = event_stream
    else:
        try:
            key = EventStream(event_stream)
        except ValueError as exc:
            raise UnknownEventStreamError(f"unknown event stream: {event_stream!r}") from exc
    descriptor = _REGISTRY.get(key)
    if descriptor is None:  # pragma: no cover - defensive; every enum member is registered
        raise UnknownEventStreamError(f"no source contract registered for stream: {key!r}")
    return descriptor


def list_source_contracts() -> tuple[SourceContractDescriptor, ...]:
    """Return every registered source contract, sorted by event stream value."""

    return tuple(_REGISTRY[stream] for stream in sorted(_REGISTRY, key=lambda s: s.value))


def registered_event_streams() -> frozenset[EventStream]:
    return frozenset(_REGISTRY)
