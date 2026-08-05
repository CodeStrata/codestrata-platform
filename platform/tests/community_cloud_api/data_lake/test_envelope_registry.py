"""Envelope registry lookup tests (Slice 8.3)."""

from __future__ import annotations

import pytest

from codestrata_platform.community_cloud_api.ai_usage.models import AiUsageRequest
from codestrata_platform.community_cloud_api.assessment_metadata.models import (
    AssessmentMetadataRequest,
)
from codestrata_platform.community_cloud_api.cli_events.models import CliEventRequest
from codestrata_platform.community_cloud_api.data_lake.enums import EventStream
from codestrata_platform.community_cloud_api.data_lake.envelope_registry import (
    UnknownEventStreamError,
    get_source_contract,
    list_source_contracts,
    registered_event_streams,
)
from codestrata_platform.community_cloud_api.data_lake.source_contracts import (
    SourceContractDescriptor,
)
from codestrata_platform.community_cloud_api.extension_events.models import (
    ExtensionEventRequest,
)
from codestrata_platform.community_cloud_api.telemetry.models import TelemetryIngestionRequest


def test_registered_event_streams_covers_every_enum_member() -> None:
    assert registered_event_streams() == frozenset(EventStream)


@pytest.mark.parametrize(
    "stream,expected_model,expected_schema_name",
    [
        (EventStream.TELEMETRY, TelemetryIngestionRequest, "community-telemetry"),
        (
            EventStream.ASSESSMENT_METADATA,
            AssessmentMetadataRequest,
            "community-assessment-metadata",
        ),
        (EventStream.CLI_EVENT, CliEventRequest, "community-cli-event"),
        (EventStream.EXTENSION_EVENT, ExtensionEventRequest, "community-extension-event"),
        (EventStream.AI_USAGE, AiUsageRequest, "community-ai-usage"),
    ],
)
def test_get_source_contract_resolves_every_stream(
    stream: EventStream, expected_model: type, expected_schema_name: str
) -> None:
    descriptor = get_source_contract(stream)
    assert isinstance(descriptor, SourceContractDescriptor)
    assert descriptor.event_stream is stream
    assert descriptor.request_model is expected_model
    assert descriptor.schema_name == expected_schema_name
    assert descriptor.schema_version == "1.0"
    assert descriptor.policy_id.endswith(":1.0")
    assert ":" in descriptor.policy_id


def test_get_source_contract_accepts_string_stream_value() -> None:
    descriptor = get_source_contract("telemetry")
    assert descriptor.event_stream is EventStream.TELEMETRY


def test_get_source_contract_rejects_unknown_string() -> None:
    with pytest.raises(UnknownEventStreamError):
        get_source_contract("not_a_real_stream")


def test_get_source_contract_rejects_empty_string() -> None:
    with pytest.raises(UnknownEventStreamError):
        get_source_contract("")


def test_list_source_contracts_returns_all_five_sorted_by_stream_value() -> None:
    contracts = list_source_contracts()
    assert len(contracts) == 5
    values = [contract.event_stream.value for contract in contracts]
    assert values == sorted(values)


def test_every_descriptor_has_nonempty_allowed_client_types() -> None:
    for descriptor in list_source_contracts():
        assert descriptor.allowed_client_types
        assert isinstance(descriptor.allowed_client_types, frozenset)


def test_every_descriptor_project_payload_and_client_type_extractor_are_callable() -> None:
    for descriptor in list_source_contracts():
        assert callable(descriptor.project_payload)
        assert callable(descriptor.client_type_extractor)


def test_cli_event_descriptor_carries_operation_catalog_version_metadata() -> None:
    descriptor = get_source_contract(EventStream.CLI_EVENT)
    assert "operation_catalog_version" in descriptor.catalog_versions


def test_extension_event_descriptor_carries_operation_catalog_version_metadata() -> None:
    descriptor = get_source_contract(EventStream.EXTENSION_EVENT)
    assert "operation_catalog_version" in descriptor.catalog_versions


def test_ai_usage_descriptor_carries_catalog_version_metadata() -> None:
    descriptor = get_source_contract(EventStream.AI_USAGE)
    catalog_versions = descriptor.catalog_versions
    assert "capability_catalog_version" in catalog_versions
    assert "model_catalog_version" in catalog_versions
    assert "provider_catalog_version" in catalog_versions


def test_telemetry_and_assessment_metadata_descriptors_have_no_catalog_versions() -> None:
    assert get_source_contract(EventStream.TELEMETRY).catalog_versions == {}
    assert get_source_contract(EventStream.ASSESSMENT_METADATA).catalog_versions == {}


def test_descriptor_to_stable_dict_is_sorted_and_json_safe() -> None:
    descriptor = get_source_contract(EventStream.TELEMETRY)
    blob = descriptor.to_stable_dict()
    assert list(blob) == sorted(blob)
    assert blob["event_stream"] == "telemetry"
    assert blob["schema_name"] == "community-telemetry"
