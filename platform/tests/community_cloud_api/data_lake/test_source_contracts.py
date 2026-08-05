"""SourceContractDescriptor structural validation tests (Slice 8.3)."""

from __future__ import annotations

import pytest

from codestrata_platform.community_cloud_api.data_lake.enums import EventStream
from codestrata_platform.community_cloud_api.data_lake.source_contracts import (
    SourceContractDescriptor,
    SourceContractError,
)
from codestrata_platform.community_cloud_api.telemetry.models import TelemetryIngestionRequest


def _kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = dict(
        event_stream=EventStream.TELEMETRY,
        schema_name="community-telemetry",
        schema_version="1.0",
        policy_id="community-telemetry-policy:1.0",
        request_model=TelemetryIngestionRequest,
        allowed_client_types=frozenset({"codestrata_cli"}),
        project_payload=lambda request: request.to_stable_dict(),
        client_type_extractor=lambda request: request.client.name,
    )
    base.update(overrides)
    return base


def test_valid_descriptor_constructs() -> None:
    descriptor = SourceContractDescriptor(**_kwargs())
    assert descriptor.event_stream is EventStream.TELEMETRY
    assert descriptor.catalog_versions == {}


def test_rejects_non_event_stream_member() -> None:
    with pytest.raises(SourceContractError):
        SourceContractDescriptor(**_kwargs(event_stream="telemetry"))


def test_rejects_blank_schema_name() -> None:
    with pytest.raises(SourceContractError):
        SourceContractDescriptor(**_kwargs(schema_name=""))


def test_rejects_blank_schema_version() -> None:
    with pytest.raises(SourceContractError):
        SourceContractDescriptor(**_kwargs(schema_version=""))


def test_rejects_policy_id_missing_urn_separator() -> None:
    with pytest.raises(SourceContractError):
        SourceContractDescriptor(**_kwargs(policy_id="community-telemetry-policy"))


def test_rejects_blank_policy_id() -> None:
    with pytest.raises(SourceContractError):
        SourceContractDescriptor(**_kwargs(policy_id=""))


def test_rejects_request_model_not_a_type() -> None:
    with pytest.raises(SourceContractError):
        SourceContractDescriptor(**_kwargs(request_model="not-a-type"))


def test_rejects_request_model_not_a_community_api_request_model_subclass() -> None:
    class NotARequestModel:
        pass

    with pytest.raises(SourceContractError):
        SourceContractDescriptor(**_kwargs(request_model=NotARequestModel))


def test_rejects_empty_allowed_client_types() -> None:
    with pytest.raises(SourceContractError):
        SourceContractDescriptor(**_kwargs(allowed_client_types=frozenset()))


def test_allowed_client_types_is_normalized_to_frozenset() -> None:
    descriptor = SourceContractDescriptor(**_kwargs(allowed_client_types={"a", "b"}))
    assert descriptor.allowed_client_types == frozenset({"a", "b"})


def test_catalog_versions_is_normalized_to_plain_dict() -> None:
    descriptor = SourceContractDescriptor(**_kwargs(catalog_versions={"x": "1"}))
    assert descriptor.catalog_versions == {"x": "1"}
    assert isinstance(descriptor.catalog_versions, dict)


def test_to_stable_dict_sorts_allowed_client_types_and_catalog_versions() -> None:
    descriptor = SourceContractDescriptor(
        **_kwargs(
            allowed_client_types={"zeta", "alpha"},
            catalog_versions={"z": "9", "a": "1"},
        )
    )
    blob = descriptor.to_stable_dict()
    assert blob["allowed_client_types"] == ["alpha", "zeta"]
    assert blob["catalog_versions"] == {"a": "1", "z": "9"}
    assert list(blob) == sorted(blob)
