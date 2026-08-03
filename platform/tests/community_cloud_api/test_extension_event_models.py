"""Extension event model and catalog tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from codestrata_platform.community_cloud_api.extension_events.catalog import (
    EXTENSION_OPERATION_CATALOG_URN,
    ExtensionOperationCatalog,
)
from codestrata_platform.community_cloud_api.extension_events.models import (
    ExtensionEventRequest,
)
from codestrata_platform.community_cloud_api.extension_events.policy import (
    COMMUNITY_EXTENSION_EVENT_POLICY_URN,
    CommunityExtensionEventPolicy,
)

from .extension_event_helpers import valid_extension_event_body


def test_required_fields_and_canonical_operation() -> None:
    model = ExtensionEventRequest.model_validate(valid_extension_event_body())
    assert model.client.name == "vscode_extension"
    assert model.client.editor == "vscode"
    assert model.event.operation == "assess"
    assert model.context.selected_assessment_heads == [
        "security",
        "technology_inventory",
    ]


def test_alias_canonicalized_and_cursor_client() -> None:
    body = valid_extension_event_body()
    body["event"] = {**body["event"], "operation": "codestrata.openHtmlReport"}  # type: ignore[dict-item]
    model = ExtensionEventRequest.model_validate(body)
    assert model.event.operation == "open_report"

    cursor = valid_extension_event_body()
    cursor["client"] = {
        "name": "cursor_extension",
        "version": "0.2.0",
        "editor": "cursor",
        "editor_version": "0.45.0",
        "platform": "darwin",
    }
    ExtensionEventRequest.model_validate(cursor)


def test_cli_and_mismatched_editor_rejected() -> None:
    body = valid_extension_event_body()
    body["client"] = {
        "name": "codestrata_cli",
        "version": "0.2.0",
        "editor": "vscode",
        "editor_version": "1.85.0",
        "platform": "darwin",
    }
    with pytest.raises(ValidationError):
        ExtensionEventRequest.model_validate(body)

    mismatch = valid_extension_event_body()
    mismatch["client"] = {
        "name": "vscode_extension",
        "version": "0.2.0",
        "editor": "cursor",
        "editor_version": "1.85.0",
        "platform": "darwin",
    }
    with pytest.raises(ValidationError):
        ExtensionEventRequest.model_validate(mismatch)

    other = valid_extension_event_body()
    other["client"] = {
        "name": "other_extension",
        "version": "0.2.0",
        "editor": "vscode",
        "editor_version": "1.85.0",
        "platform": "darwin",
    }
    with pytest.raises(ValidationError):
        ExtensionEventRequest.model_validate(other)


def test_failure_category_rules() -> None:
    body = valid_extension_event_body()
    body["event"] = {
        "operation": "assess",
        "lifecycle": "failed",
        "result": "failed",
        "duration_bucket": "unavailable",
    }
    with pytest.raises(ValidationError):
        ExtensionEventRequest.model_validate(body)
    body["event"]["failure_category"] = "assessment_failed"  # type: ignore[index]
    ExtensionEventRequest.model_validate(body)
    ok = valid_extension_event_body()
    ok["event"] = {**ok["event"], "failure_category": "internal_error"}  # type: ignore[dict-item]
    with pytest.raises(ValidationError):
        ExtensionEventRequest.model_validate(ok)


def test_policy_and_catalog_stable() -> None:
    policy = CommunityExtensionEventPolicy.default()
    assert policy.policy_token == COMMUNITY_EXTENSION_EVENT_POLICY_URN
    catalog = ExtensionOperationCatalog.default()
    assert catalog.catalog_token == EXTENSION_OPERATION_CATALOG_URN
    assert catalog.canonicalize("codestrata.assessWithAi") == "assess_with_ai"
    with pytest.raises(ValueError):
        CommunityExtensionEventPolicy(policy_version="9.9")
