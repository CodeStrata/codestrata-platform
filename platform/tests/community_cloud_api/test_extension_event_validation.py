"""Extension event privacy validation tests."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from codestrata_platform.community_cloud_api.extension_events.models import (
    ExtensionEventRequest,
)
from codestrata_platform.community_cloud_api.extension_events.routes import (
    extension_event_request_schema,
)
from codestrata_platform.community_cloud_api.validation.validator import validate_request_body

from .extension_event_helpers import valid_extension_event_body


@pytest.mark.parametrize(
    "field",
    [
        "workspace_name",
        "workspace_uri",
        "workspace_path",
        "repository",
        "repository_url",
        "document",
        "document_uri",
        "file",
        "file_path",
        "active_file",
        "open_tabs",
        "selected_text",
        "cursor",
        "source",
        "snippet",
        "clipboard",
        "terminal",
        "search",
        "settings",
        "environment",
        "extension_path",
        "email",
        "exception",
        "error_message",
        "stack_trace",
        "prompt",
        "model",
        "provider",
        "token_count",
        "cost",
        "command_id",
        "args",
    ],
)
def test_forbidden_fields_rejected(field: str) -> None:
    body = valid_extension_event_body()
    body[field] = "x"
    with pytest.raises(ValidationError):
        ExtensionEventRequest.model_validate(body)


def test_exact_duration_rejected() -> None:
    body = valid_extension_event_body()
    body["event"] = {**body["event"], "duration_ms": 1200}  # type: ignore[dict-item]
    with pytest.raises(ValidationError):
        ExtensionEventRequest.model_validate(body)


def test_api_validation_no_echo() -> None:
    body = valid_extension_event_body()
    body["workspace_path"] = "/Users/satish/secret-workspace"
    result = validate_request_body(
        descriptor=extension_event_request_schema(),
        body=json.dumps(body).encode("utf-8"),
        content_type="application/json",
        route_name="extension_events.ingest",
    )
    assert not result.valid
    blob = json.dumps([e.to_stable_dict() for e in result.errors])
    assert "secret-workspace" not in blob
    assert "/Users/" not in blob
