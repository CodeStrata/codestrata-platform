"""Telemetry request model tests (Slice 7.7)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from codestrata_platform.community_cloud_api.telemetry.enums import TelemetryEventType
from codestrata_platform.community_cloud_api.telemetry.models import (
    TelemetryClient,
    TelemetryIngestionRequest,
    TelemetryProperties,
)
from codestrata_platform.community_cloud_api.telemetry.policy import (
    COMMUNITY_TELEMETRY_POLICY_URN,
    COMMUNITY_TELEMETRY_SCHEMA_VERSION,
    CommunityTelemetryPolicy,
)


def _req(**kwargs: object) -> TelemetryIngestionRequest:
    base = {
        "schema_version": "1.0",
        "event_id": "evt-test-0001",
        "event_type": "application_started",
        "client": {
            "name": "codestrata_cli",
            "version": "0.2.0",
            "platform": "darwin",
        },
    }
    base.update(kwargs)
    return TelemetryIngestionRequest.model_validate(base)


def test_schema_version_event_id_event_type_client_required() -> None:
    model = _req()
    assert model.schema_version == COMMUNITY_TELEMETRY_SCHEMA_VERSION
    assert model.event_id == "evt-test-0001"
    assert model.event_type == "application_started"
    assert model.client.name == "codestrata_cli"
    assert model.installation_id is None
    assert model.occurred_at is None
    assert model.properties is None


def test_immutable_and_unknown_fields_rejected() -> None:
    model = _req()
    with pytest.raises(ValidationError):
        model.event_type = "feature_invoked"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        TelemetryIngestionRequest.model_validate(
            {
                "schema_version": "1.0",
                "event_id": "evt-test-0001",
                "event_type": "application_started",
                "client": {
                    "name": "codestrata_cli",
                    "version": "0.2.0",
                    "platform": "darwin",
                },
                "extra": True,
            }
        )


def test_optional_installation_and_occurred_at() -> None:
    model = _req(
        installation_id="install-abcdef12",
        occurred_at="2026-07-29T18:00:00Z",
    )
    assert model.installation_id == "install-abcdef12"
    assert model.occurred_at == "2026-07-29T18:00:00Z"


def test_properties_bounded() -> None:
    model = _req(
        properties={
            "feature": "assess",
            "operation": "run",
            "outcome": "succeeded",
            "duration_bucket": "1s_to_5s",
            "count": 2,
            "flags": ["local"],
        }
    )
    assert model.properties is not None
    assert model.properties.count == 2


def test_top_level_array_rejected() -> None:
    with pytest.raises(ValidationError):
        TelemetryIngestionRequest.model_validate([{"schema_version": "1.0"}])


def test_client_allowlist_and_unknown_fields() -> None:
    TelemetryClient.model_validate(
        {"name": "vscode_extension", "version": "1.0.0", "platform": "linux"}
    )
    with pytest.raises(ValidationError):
        TelemetryClient.model_validate(
            {"name": "browser", "version": "1.0.0", "platform": "linux"}
        )
    with pytest.raises(ValidationError):
        TelemetryClient.model_validate(
            {
                "name": "codestrata_cli",
                "version": "1.0.0",
                "platform": "linux",
                "hostname": "box",
            }
        )


def test_event_types_allowlisted() -> None:
    for item in TelemetryEventType:
        _req(event_type=item.value)
    with pytest.raises(ValidationError):
        _req(event_type="click")
    with pytest.raises(ValidationError):
        _req(event_type="assessment_started")
    with pytest.raises(ValidationError):
        _req(event_type="ai_used")


def test_properties_unknown_and_raw_duration_rejected() -> None:
    with pytest.raises(ValidationError):
        TelemetryProperties.model_validate({"metadata": {"a": 1}})
    with pytest.raises(ValidationError):
        TelemetryProperties.model_validate({"duration_ms": 12})
    with pytest.raises(ValidationError):
        TelemetryProperties.model_validate({"outcome": "boom"})
    with pytest.raises(ValidationError):
        TelemetryProperties.model_validate({"count": -1})
    with pytest.raises(ValidationError):
        TelemetryProperties.model_validate({"count": 10001})


def test_policy_token_stable() -> None:
    policy = CommunityTelemetryPolicy.default()
    assert policy.policy_token == COMMUNITY_TELEMETRY_POLICY_URN
    assert policy.telemetry_schema_version == "1.0"
    assert policy.to_stable_dict() == CommunityTelemetryPolicy.default().to_stable_dict()
    with pytest.raises(ValueError):
        CommunityTelemetryPolicy(policy_version="9.9")
