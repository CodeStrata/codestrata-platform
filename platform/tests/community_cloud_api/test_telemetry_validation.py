"""Telemetry privacy and property validation tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from codestrata_platform.community_cloud_api.telemetry.models import (
    TelemetryIngestionRequest,
    TelemetryProperties,
)
from codestrata_platform.community_cloud_api.telemetry.validation import (
    validate_telemetry_semantics,
)


def _base(**kwargs: object) -> dict[str, object]:
    body: dict[str, object] = {
        "schema_version": "1.0",
        "event_id": "evt-test-0001",
        "event_type": "feature_invoked",
        "client": {
            "name": "codestrata_cli",
            "version": "0.2.0",
            "platform": "darwin",
        },
    }
    body.update(kwargs)
    return body


@pytest.mark.parametrize(
    "props",
    [
        {"feature": "user@example.com"},
        {"operation": "/Users/satish/project"},
        {"feature": "C:\\Windows\\system32"},
        {"feature": "file://secret"},
        {"feature": "https://example.com/repo"},
        {"operation": "def foo():\n  return 1"},
        {"feature": "Bearer supersecrettokenvalue"},
        {"flags": ["AKIAIOSFODNN7EXAMPLE"]},
    ],
)
def test_secret_path_url_code_rejected(props: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        TelemetryProperties.model_validate(props)


@pytest.mark.parametrize(
    "forbidden_field",
    [
        "email",
        "username",
        "repository_name",
        "repository_url",
        "prompt",
        "token",
        "stack_trace",
        "command_args",
        "source_code",
    ],
)
def test_forbidden_property_field_names_rejected(forbidden_field: str) -> None:
    with pytest.raises(ValidationError):
        TelemetryProperties.model_validate({forbidden_field: "x"})


def test_nested_arbitrary_object_rejected() -> None:
    with pytest.raises(ValidationError):
        TelemetryProperties.model_validate({"feature": {"nested": True}})


def test_no_rejected_value_echoed_in_api_validation_errors() -> None:
    from codestrata_platform.community_cloud_api.telemetry.routes import (
        telemetry_request_schema,
    )
    from codestrata_platform.community_cloud_api.validation.validator import (
        validate_request_body,
    )
    import json

    body = json.dumps(
        _base(properties={"feature": "user@example.com"})
    ).encode("utf-8")
    result = validate_request_body(
        descriptor=telemetry_request_schema(),
        body=body,
        content_type="application/json",
        route_name="telemetry.ingest",
    )
    assert not result.valid
    blob = json.dumps([err.to_stable_dict() for err in result.errors])
    assert "user@example.com" not in blob
    assert all("@" not in err.message for err in result.errors)


def test_semantic_validator_rejects_bad_schema() -> None:
    # Construct via model_construct to bypass Literal, then semantic fails.
    model = TelemetryIngestionRequest.model_construct(
        schema_version="9.0",  # type: ignore[arg-type]
        event_id="evt-test-0001",
        event_type="application_started",
        client=TelemetryIngestionRequest.model_validate(_base()).client,
        installation_id=None,
        occurred_at=None,
        properties=None,
    )
    errors = validate_telemetry_semantics(model)
    assert any(item.field == "schema_version" for item in errors)
