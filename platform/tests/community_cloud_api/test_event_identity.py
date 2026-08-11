"""ApiEventId, scope, event-key, and validation integration tests."""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

import json

import pytest
from fastapi.testclient import TestClient

from codestrata_platform.community_cloud_api import (
    COMMUNITY_EVENT_IDENTITY_POLICY_URN,
    CommunityEventIdentityPolicy,
    RouteRegistry,
    RouteSpec,
    create_community_cloud_app,
)
from codestrata_platform.community_cloud_api.event_identity import (
    EventIdentityScope,
    build_event_key,
    build_safe_event_reference,
    validate_event_id_text,
)
from codestrata_platform.community_cloud_api.models import RequestContext
from codestrata_platform.community_cloud_api.serialization import build_json_response
from codestrata_platform.community_cloud_api.validation import (
    ApiClientName,
    ApiEventId,
    ApiEventName,
    BodyPolicy,
    CommunityApiRequestModel,
    RequestSchemaDescriptor,
)
from codestrata_platform.community_cloud_api.validation.errors import FIELD_UNSAFE_VALUE
from starlette.responses import Response


class EventIdProbeRequest(CommunityApiRequestModel):
    event_id: ApiEventId
    event_type: ApiEventName
    client_name: ApiClientName


def _handle(context: RequestContext) -> Response:
    body = context.validated_request
    assert isinstance(body, EventIdProbeRequest)
    return build_json_response(
        {"accepted": True, "has_event_id": True},
        status_code=200,
        api_version="v1",
        request_id=context.request_id,
    )


def test_api_event_id_accepts_opaque_forms() -> None:
    for value in (
        "abcd1234",
        "550e8400-e29b-41d4-a716-446655440000",
        "01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "cli:run-abc_123",
    ):
        assert validate_event_id_text(value) == value


def test_api_event_id_rejects_unsafe_and_invalid() -> None:
    cases = [
        ("short", "too_short"),
        ("x" * 129, "too_long"),
        ("has space1", "unsafe_value"),
        ("has\nnewline", "unsafe_value"),
        ("has/slashx", "invalid_format"),
        ("has\\slashx", "invalid_format"),
        ("file:///etc/passwd", "unsafe_value"),
        ("/Users/satish/id", "unsafe_value"),
        ("Bearer supersecrettoken", "unsafe_value"),
        ("-----BEGIN PRIVATE KEY-----abcdef", "unsafe_value"),
    ]
    for value, _code in cases:
        with pytest.raises(ValueError):
            validate_event_id_text(value)


def test_api_event_id_not_echoed_in_validation_error() -> None:
    from codestrata_platform.community_cloud_api.validation import (
        BodyPolicy,
        RequestSchemaDescriptor,
        validate_request_body,
    )

    class M(CommunityApiRequestModel):
        event_id: ApiEventId

    secret = "Bearer supersecrettokenvalue"
    result = validate_request_body(
        descriptor=RequestSchemaDescriptor(
            schema_id="community.test.event-id-echo",
            schema_version="1.0",
            model_type=M,
            body_policy=BodyPolicy.REQUIRED,
        ),
        body=json.dumps({"event_id": secret}).encode(),
        content_type="application/json",
    )
    assert not result.valid
    blob = json.dumps([item.to_stable_dict() for item in result.errors])
    assert secret not in blob
    assert "Bearer" not in blob
    assert any(item.code == FIELD_UNSAFE_VALUE for item in result.errors)


def test_policy_token_stable() -> None:
    policy = CommunityEventIdentityPolicy.default()
    assert policy.policy_token == COMMUNITY_EVENT_IDENTITY_POLICY_URN
    assert policy.policy_token == "community-event-identity-policy:1.0"
    assert policy.to_stable_dict()["policy_token"] == policy.policy_token
    assert f"{policy.policy_id}:2.0" != policy.policy_token


def test_policy_rejects_bad_bounds_and_exclusions() -> None:
    with pytest.raises(ValueError):
        CommunityEventIdentityPolicy(event_id_min_length=2)
    with pytest.raises(ValueError):
        CommunityEventIdentityPolicy(
            fingerprint_excluded_fields=("event_id", "request_id")
        )


def test_scope_equality_and_differences() -> None:
    base = EventIdentityScope(
        api_version="v1",
        client_type="cli",
        event_type="cli.started",
        event_id="evt-aaaa1111",
        installation_id="install01",
    )
    same = EventIdentityScope(
        api_version="v1",
        client_type="cli",
        event_type="cli.started",
        event_id="evt-aaaa1111",
        installation_id="install01",
    )
    assert base == same
    assert base.to_stable_dict() == same.to_stable_dict()
    assert build_event_key(base) != build_event_key(
        EventIdentityScope(
            api_version="v1",
            client_type="cli",
            event_type="cli.finished",
            event_id="evt-aaaa1111",
            installation_id="install01",
        )
    )
    assert build_event_key(base) != build_event_key(
        EventIdentityScope(
            api_version="v1",
            client_type="vscode_extension",
            event_type="cli.started",
            event_id="evt-aaaa1111",
            installation_id="install01",
        )
    )
    assert build_event_key(base) != build_event_key(
        EventIdentityScope(
            api_version="v1",
            client_type="cli",
            event_type="cli.started",
            event_id="evt-aaaa1111",
            installation_id="install02",
        )
    )


def test_event_key_deterministic_and_opaque() -> None:
    scope = EventIdentityScope(
        api_version="v1",
        client_type="cli",
        event_type="cli.started",
        event_id="evt-aaaa1111",
    )
    left = build_event_key(scope)
    right = build_event_key(scope)
    assert left == right
    assert left.startswith("event:")
    assert "evt-aaaa1111" not in left
    assert len(left) == len("event:") + 24


def test_safe_event_reference() -> None:
    key = build_event_key(
        EventIdentityScope(
            api_version="v1",
            client_type="cli",
            event_type="cli.started",
            event_id="evt-aaaa1111",
        )
    )
    ref = build_safe_event_reference(key)
    assert ref == build_safe_event_reference(key)
    assert ref.startswith("evt-")
    assert len(ref) == 4 + 12
    assert "evt-aaaa1111" not in ref
    assert key not in ref


def test_validation_integration_test_only_route() -> None:
    registry = RouteRegistry.foundation_v1()
    registry.register(
        RouteSpec(
            version="v1",
            method="POST",
            path="/_test/event-id-probe",
            name="test.event_id_probe",
        ),
        handler=_handle,
        request_schema=RequestSchemaDescriptor(
            schema_id="community.test.event-id-probe",
            schema_version="1.0",
            model_type=EventIdProbeRequest,
            body_policy=BodyPolicy.REQUIRED,
        ),
    )
    client = TestClient(create_community_cloud_app(registry=registry,
        authentication_policy=disabled_authentication_policy(),
    ))
    ok = client.post(
        "/api/v1/_test/event-id-probe",
        json={
            "event_id": "cli:run-abc_123",
            "event_type": "cli.started",
            "client_name": "codestrata-cli",
        },
    )
    assert ok.status_code == 200
    bad = client.post(
        "/api/v1/_test/event-id-probe",
        json={
            "event_id": "Bearer supersecrettokenvalue",
            "event_type": "cli.started",
            "client_name": "codestrata-cli",
        },
    )
    assert bad.status_code == 422
    assert "supersecrettokenvalue" not in bad.text
    details = bad.json()["error"]["details"]
    assert any(item["code"] == FIELD_UNSAFE_VALUE for item in details)

    # Production registry is health + telemetry + assessment-metadata.
    prod = create_community_cloud_app(authentication_policy=disabled_authentication_policy())
    paths = {(r.method, r.path) for r in prod.state.community_cloud_route_registry.list_routes()}
    assert paths >= {("GET", "/health"), ("POST", "/ai-usage"), ("POST", "/assessment-metadata"), ("POST", "/cli-events"), ("POST", "/extension-events"), ("POST", "/telemetry")}
