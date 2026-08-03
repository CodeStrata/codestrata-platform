"""CLI event model and catalog tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from codestrata_platform.community_cloud_api.cli_events.catalog import (
    CLI_OPERATION_CATALOG_URN,
    CliOperationCatalog,
)
from codestrata_platform.community_cloud_api.cli_events.models import CliEventRequest
from codestrata_platform.community_cloud_api.cli_events.policy import (
    COMMUNITY_CLI_EVENT_POLICY_URN,
    CommunityCliEventPolicy,
)

from .cli_event_helpers import valid_cli_event_body


def test_required_fields_and_canonical_operation() -> None:
    model = CliEventRequest.model_validate(valid_cli_event_body())
    assert model.client.name == "codestrata_cli"
    assert model.event.operation == "assess"
    assert model.context.selected_assessment_heads == [
        "security",
        "technology_inventory",
    ]


def test_alias_canonicalized() -> None:
    body = valid_cli_event_body()
    body["event"] = {**body["event"], "operation": "report.open"}  # type: ignore[dict-item]
    model = CliEventRequest.model_validate(body)
    assert model.event.operation == "open"


def test_extension_client_and_unknown_operation_rejected() -> None:
    body = valid_cli_event_body()
    body["client"] = {
        "name": "vscode_extension",
        "version": "0.2.0",
        "platform": "darwin",
    }
    with pytest.raises(ValidationError):
        CliEventRequest.model_validate(body)
    body = valid_cli_event_body()
    body["event"] = {**body["event"], "operation": "rm -rf /"}  # type: ignore[dict-item]
    with pytest.raises(ValidationError):
        CliEventRequest.model_validate(body)


def test_failure_category_rules() -> None:
    body = valid_cli_event_body()
    body["event"] = {
        "operation": "assess",
        "lifecycle": "failed",
        "result": "failed",
        "duration_bucket": "unavailable",
    }
    with pytest.raises(ValidationError):
        CliEventRequest.model_validate(body)
    body["event"]["failure_category"] = "assessment_failed"  # type: ignore[index]
    CliEventRequest.model_validate(body)
    ok = valid_cli_event_body()
    ok["event"] = {**ok["event"], "failure_category": "internal_error"}  # type: ignore[dict-item]
    with pytest.raises(ValidationError):
        CliEventRequest.model_validate(ok)


def test_policy_and_catalog_stable() -> None:
    policy = CommunityCliEventPolicy.default()
    assert policy.policy_token == COMMUNITY_CLI_EVENT_POLICY_URN
    catalog = CliOperationCatalog.default()
    assert catalog.catalog_token == CLI_OPERATION_CATALOG_URN
    assert catalog.canonicalize("report_open") == "open"
    with pytest.raises(ValueError):
        CommunityCliEventPolicy(policy_version="9.9")
