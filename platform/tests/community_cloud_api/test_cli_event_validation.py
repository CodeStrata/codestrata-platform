"""CLI event privacy validation tests."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from codestrata_platform.community_cloud_api.cli_events.models import CliEventRequest
from codestrata_platform.community_cloud_api.cli_events.routes import cli_event_request_schema
from codestrata_platform.community_cloud_api.validation.validator import validate_request_body

from .cli_event_helpers import valid_cli_event_body


@pytest.mark.parametrize(
    "field",
    [
        "command",
        "argv",
        "args",
        "cwd",
        "repository",
        "repository_url",
        "branch",
        "commit",
        "path",
        "config",
        "output_path",
        "source",
        "findings",
        "exception",
        "error_message",
        "stdout",
        "stderr",
        "environment",
        "prompt",
        "model",
        "provider",
        "token_count",
        "cost",
    ],
)
def test_forbidden_fields_rejected(field: str) -> None:
    body = valid_cli_event_body()
    body[field] = "x"
    with pytest.raises(ValidationError):
        CliEventRequest.model_validate(body)


def test_exact_duration_and_command_in_event_rejected() -> None:
    body = valid_cli_event_body()
    body["event"] = {**body["event"], "duration_ms": 1200}  # type: ignore[dict-item]
    with pytest.raises(ValidationError):
        CliEventRequest.model_validate(body)
    body = valid_cli_event_body()
    body["event"] = {**body["event"], "command": "codestrata assess"}  # type: ignore[dict-item]
    with pytest.raises(ValidationError):
        CliEventRequest.model_validate(body)


def test_api_validation_no_echo() -> None:
    body = valid_cli_event_body()
    body["cwd"] = "/Users/satish/secret-repo"
    result = validate_request_body(
        descriptor=cli_event_request_schema(),
        body=json.dumps(body).encode("utf-8"),
        content_type="application/json",
        route_name="cli_events.ingest",
    )
    assert not result.valid
    blob = json.dumps([e.to_stable_dict() for e in result.errors])
    assert "secret-repo" not in blob
    assert "/Users/" not in blob
