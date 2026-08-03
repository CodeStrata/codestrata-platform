"""CLI event endpoint tests."""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

from codestrata_platform.community_cloud_api.app import create_community_cloud_app
from codestrata_platform.community_cloud_api.cli_events.enums import CliEventIngestionStatus
from codestrata_platform.community_cloud_api.cli_events.ports import UnavailableCliEventSink
from codestrata_platform.community_cloud_api.cli_events.responses import CliEventResponse
from codestrata_platform.community_cloud_api.cli_events.routes import CLI_EVENTS_ROUTE_NAME
from codestrata_platform.community_cloud_api.errors import (
    ERROR_BODY_REQUIRED,
    ERROR_CLI_EVENT_IDENTITY_UNAVAILABLE,
    ERROR_CLI_EVENT_SINK_UNAVAILABLE,
    ERROR_MALFORMED_JSON,
    ERROR_METHOD_NOT_ALLOWED,
    ERROR_UNSUPPORTED_CLI_EVENT_SCHEMA,
    ERROR_UNSUPPORTED_CLI_OPERATION,
    ERROR_UNSUPPORTED_MEDIA_TYPE,
)
from codestrata_platform.community_cloud_api.event_identity import InMemoryEventIdentityStore
from codestrata_platform.community_cloud_api.registry import RouteRegistry
from codestrata_platform.community_cloud_api.serialization import dumps_stable
from fastapi.testclient import TestClient

from .cli_event_helpers import configured_cli_client, valid_cli_event_body


def test_route_registered() -> None:
    registry = RouteRegistry.foundation_v1()
    spec = registry.get(version="v1", method="POST", path="/cli-events")
    assert spec is not None
    assert spec.name == CLI_EVENTS_ROUTE_NAME


def test_get_body_media_schema_operation() -> None:
    client, *_ = configured_cli_client()
    assert client.get("/api/v1/cli-events").status_code == 405
    assert (
        client.get("/api/v1/cli-events").json()["error"]["code"] == ERROR_METHOD_NOT_ALLOWED
    )
    assert client.post("/api/v1/cli-events").json()["error"]["code"] == ERROR_BODY_REQUIRED
    media = client.post(
        "/api/v1/cli-events", content=b"{}", headers={"Content-Type": "text/plain"}
    )
    assert media.json()["error"]["code"] == ERROR_UNSUPPORTED_MEDIA_TYPE
    bad = client.post(
        "/api/v1/cli-events", content=b"{", headers={"Content-Type": "application/json"}
    )
    assert bad.json()["error"]["code"] == ERROR_MALFORMED_JSON
    schema = client.post("/api/v1/cli-events", json=valid_cli_event_body(schema_version="2.0"))
    assert schema.status_code == 422
    assert schema.json()["error"]["code"] == ERROR_UNSUPPORTED_CLI_EVENT_SCHEMA
    op = valid_cli_event_body()
    op["event"] = {**op["event"], "operation": "not_a_real_op"}  # type: ignore[dict-item]
    rejected = client.post("/api/v1/cli-events", json=op)
    assert rejected.status_code == 422
    assert rejected.json()["error"]["code"] == ERROR_UNSUPPORTED_CLI_OPERATION


def test_first_accepted_independent_sinks() -> None:
    client, sink, store, _, tel, meta = configured_cli_client()
    first = client.post("/api/v1/cli-events", json=valid_cli_event_body())
    assert first.status_code == 202
    body = first.json()
    assert body["status"] == "accepted"
    assert body["retry_status"] == "first_seen"
    assert "operation" not in body
    assert "event_id" not in body
    assert len(sink.events) == 1
    assert tel.events == []
    assert meta.events == []
    assert len(store._items) == 1  # noqa: SLF001
    expected = CliEventResponse(
        status=CliEventIngestionStatus.ACCEPTED,
        safe_event_reference=body["safe_event_reference"],
        retry_status=body["retry_status"],
        schema_version=body["schema_version"],
    )
    assert first.content == dumps_stable(expected)


def test_defaults_fail_closed() -> None:
    client = TestClient(create_community_cloud_app(authentication_policy=disabled_authentication_policy()))
    response = client.post("/api/v1/cli-events", json=valid_cli_event_body())
    assert response.status_code == 503
    assert response.json()["error"]["code"] == ERROR_CLI_EVENT_IDENTITY_UNAVAILABLE

    store = InMemoryEventIdentityStore()
    client2 = TestClient(
        create_community_cloud_app(
            cli_event_sink=UnavailableCliEventSink(),
            event_identity_lookup=store,
            event_identity_recorder=store,
                authentication_policy=disabled_authentication_policy(),
    )
    )
    response2 = client2.post("/api/v1/cli-events", json=valid_cli_event_body())
    assert response2.status_code == 503
    assert response2.json()["error"]["code"] == ERROR_CLI_EVENT_SINK_UNAVAILABLE


def test_six_production_routes_and_health() -> None:
    client, *_ = configured_cli_client()
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.headers["Cache-Control"] == "no-store"
    paths = {
        (r.method, r.path)
        for r in create_community_cloud_app(authentication_policy=disabled_authentication_policy()).state.community_cloud_route_registry.list_routes()
    }
    assert paths == {
        ("GET", "/health"),
        ("POST", "/ai-usage"),
        ("POST", "/assessment-metadata"),
        ("POST", "/cli-events"),
        ("POST", "/extension-events"),
        ("POST", "/telemetry"),
    }
