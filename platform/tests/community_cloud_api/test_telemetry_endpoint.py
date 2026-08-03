"""Telemetry endpoint route and acceptance tests."""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

from codestrata_platform.community_cloud_api.app import create_community_cloud_app
from codestrata_platform.community_cloud_api.errors import (
    ERROR_BODY_REQUIRED,
    ERROR_EVENT_IDENTITY_UNAVAILABLE,
    ERROR_MALFORMED_JSON,
    ERROR_METHOD_NOT_ALLOWED,
    ERROR_TELEMETRY_SINK_UNAVAILABLE,
    ERROR_UNSUPPORTED_MEDIA_TYPE,
    ERROR_UNSUPPORTED_TELEMETRY_EVENT,
    ERROR_UNSUPPORTED_TELEMETRY_SCHEMA,
)
from codestrata_platform.community_cloud_api.event_identity import InMemoryEventIdentityStore
from codestrata_platform.community_cloud_api.registry import RouteRegistry
from codestrata_platform.community_cloud_api.serialization import dumps_stable
from codestrata_platform.community_cloud_api.telemetry.enums import TelemetryIngestionStatus
from codestrata_platform.community_cloud_api.telemetry.ports import (
    UnavailableTelemetryEventSink,
)
from codestrata_platform.community_cloud_api.telemetry.responses import (
    TelemetryIngestionResponse,
)
from codestrata_platform.community_cloud_api.telemetry.routes import TELEMETRY_ROUTE_NAME
from fastapi.testclient import TestClient

from .telemetry_helpers import configured_client, valid_telemetry_body


def test_post_telemetry_registered_through_v1_registry() -> None:
    registry = RouteRegistry.foundation_v1()
    spec = registry.get(version="v1", method="POST", path="/telemetry")
    assert spec is not None
    assert spec.name == TELEMETRY_ROUTE_NAME
    assert registry.get_handler(spec) is not None
    assert registry.get_request_schema(spec) is not None


def test_get_rejected_body_and_content_type_required() -> None:
    client, *_ = configured_client()
    assert client.get("/api/v1/telemetry").status_code == 405
    assert (
        client.get("/api/v1/telemetry").json()["error"]["code"] == ERROR_METHOD_NOT_ALLOWED
    )
    missing = client.post("/api/v1/telemetry")
    assert missing.status_code == 400
    assert missing.json()["error"]["code"] == ERROR_BODY_REQUIRED
    media = client.post(
        "/api/v1/telemetry",
        content=b"{}",
        headers={"Content-Type": "text/plain"},
    )
    assert media.status_code == 415
    assert media.json()["error"]["code"] == ERROR_UNSUPPORTED_MEDIA_TYPE


def test_malformed_json_and_schema_invalid() -> None:
    client, *_ = configured_client()
    bad = client.post(
        "/api/v1/telemetry",
        content=b"{",
        headers={"Content-Type": "application/json"},
    )
    assert bad.status_code == 400
    assert bad.json()["error"]["code"] == ERROR_MALFORMED_JSON

    schema = client.post("/api/v1/telemetry", json=valid_telemetry_body(schema_version="2.0"))
    assert schema.status_code == 422
    assert schema.json()["error"]["code"] == ERROR_UNSUPPORTED_TELEMETRY_SCHEMA

    event = client.post(
        "/api/v1/telemetry",
        json=valid_telemetry_body(event_type="assessment_started"),
    )
    assert event.status_code == 422
    assert event.json()["error"]["code"] == ERROR_UNSUPPORTED_TELEMETRY_EVENT


def test_first_accepted_202_deterministic() -> None:
    client, sink, store, _ = configured_client()
    first = client.post("/api/v1/telemetry", json=valid_telemetry_body())
    assert first.status_code == 202
    body = first.json()
    assert body["status"] == "accepted"
    assert body["retry_status"] == "first_seen"
    assert body["schema_version"] == "1.0"
    assert body["safe_event_reference"].startswith("evt-")
    assert "event_id" not in body
    assert "installation_id" not in body
    assert "event_key" not in body
    assert "payload_fingerprint" not in body
    assert list(body.keys()) == sorted(body.keys())
    assert len(sink.events) == 1
    assert len(store._items) == 1  # noqa: SLF001 - test store internals
    assert "event_id" not in sink.events[0].to_stable_dict()
    assert "installation_id" not in sink.events[0].to_stable_dict()

    expected = TelemetryIngestionResponse(
        status=TelemetryIngestionStatus.ACCEPTED,
        safe_event_reference=body["safe_event_reference"],
        retry_status=body["retry_status"],
        schema_version=body["schema_version"],
    )
    assert first.content == dumps_stable(expected)


def test_default_app_fail_closed_without_identity() -> None:
    client = TestClient(create_community_cloud_app(authentication_policy=disabled_authentication_policy()))
    response = client.post("/api/v1/telemetry", json=valid_telemetry_body())
    assert response.status_code == 503
    assert response.json()["error"]["code"] == ERROR_EVENT_IDENTITY_UNAVAILABLE


def test_unavailable_sink_503() -> None:
    store = InMemoryEventIdentityStore()
    client = TestClient(
        create_community_cloud_app(
            telemetry_sink=UnavailableTelemetryEventSink(),
            event_identity_lookup=store,
            event_identity_recorder=store,
                authentication_policy=disabled_authentication_policy(),
    )
    )
    response = client.post("/api/v1/telemetry", json=valid_telemetry_body())
    assert response.status_code == 503
    assert response.json()["error"]["code"] == ERROR_TELEMETRY_SINK_UNAVAILABLE


def test_payload_limits_still_apply() -> None:
    client, *_ = configured_client()
    huge = valid_telemetry_body()
    huge["client"] = {
        "name": "codestrata_cli",
        "version": "0.2.0",
        "platform": "x" * 5000,
    }
    response = client.post("/api/v1/telemetry", json=huge)
    assert response.status_code in {413, 422}


def test_health_unchanged_with_telemetry_route() -> None:
    client, *_ = configured_client()
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.headers["Cache-Control"] == "no-store"


def test_only_six_production_routes() -> None:
    paths = {
        (r.method, r.path)
        for r in create_community_cloud_app(authentication_policy=disabled_authentication_policy()).state.community_cloud_route_registry.list_routes()
    }
    assert paths == {("GET", "/health"), ("POST", "/ai-usage"), ("POST", "/assessment-metadata"), ("POST", "/cli-events"), ("POST", "/extension-events"), ("POST", "/telemetry")}
