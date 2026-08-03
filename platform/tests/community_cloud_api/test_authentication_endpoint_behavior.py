"""Authentication endpoint behavior tests."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.app import create_community_cloud_app
from codestrata_platform.community_cloud_api.errors import (
    ERROR_AUTHENTICATION_REQUIRED,
    ERROR_AUTHENTICATION_UNAVAILABLE,
    ERROR_CLIENT_NOT_AUTHORIZED,
    ERROR_INVALID_CLIENT_CREDENTIAL,
)
from codestrata_platform.community_cloud_api.event_identity import InMemoryEventIdentityStore
from codestrata_platform.community_cloud_api.telemetry.ports import InMemoryTelemetryEventSink
from fastapi.testclient import TestClient

from .auth_test_support import (
    TEST_CLI_TOKEN,
    TEST_VSCODE_TOKEN,
    auth_headers,
    build_test_verifier,
)
from .telemetry_helpers import valid_telemetry_body


def _authed_client(**kwargs: object) -> tuple[TestClient, InMemoryTelemetryEventSink]:
    sink = InMemoryTelemetryEventSink()
    store = InMemoryEventIdentityStore()
    verifier = build_test_verifier()
    app = create_community_cloud_app(
        telemetry_sink=sink,
        event_identity_lookup=store,
        event_identity_recorder=store,
        credential_verifier=verifier,
        **kwargs,  # type: ignore[arg-type]
    )
    return TestClient(app), sink


def test_health_public_and_default_verifier_unavailable() -> None:
    client = TestClient(create_community_cloud_app())
    assert client.get("/api/v1/health").status_code == 200
    blocked = client.post("/api/v1/telemetry", json=valid_telemetry_body())
    assert blocked.status_code == 503
    assert blocked.json()["error"]["code"] == ERROR_AUTHENTICATION_UNAVAILABLE


def test_missing_and_invalid_auth() -> None:
    client, sink = _authed_client()
    missing = client.post("/api/v1/telemetry", json=valid_telemetry_body())
    assert missing.status_code == 401
    assert missing.json()["error"]["code"] == ERROR_AUTHENTICATION_REQUIRED
    assert missing.headers.get("WWW-Authenticate") == "Bearer"
    invalid = client.post(
        "/api/v1/telemetry",
        json=valid_telemetry_body(),
        headers=auth_headers("cscc_v1_TEST_ONLY_UNKNOWN_TOKEN_ZZ"),
    )
    assert invalid.status_code == 401
    assert invalid.json()["error"]["code"] == ERROR_INVALID_CLIENT_CREDENTIAL
    assert TEST_CLI_TOKEN not in invalid.text
    assert len(sink.events) == 0


def test_valid_auth_and_client_type_mismatch() -> None:
    client, sink = _authed_client()
    ok = client.post(
        "/api/v1/telemetry",
        json=valid_telemetry_body(),
        headers=auth_headers(TEST_CLI_TOKEN),
    )
    assert ok.status_code == 202
    assert len(sink.events) == 1
    mismatch = client.post(
        "/api/v1/telemetry",
        json=valid_telemetry_body(
            event_id="evt-mismatch-0001",
            client={"name": "vscode_extension", "version": "0.2.0", "platform": "darwin"},
        ),
        headers=auth_headers(TEST_CLI_TOKEN),
    )
    assert mismatch.status_code == 403
    assert mismatch.json()["error"]["code"] == ERROR_CLIENT_NOT_AUTHORIZED
    vscode_ok = client.post(
        "/api/v1/telemetry",
        json=valid_telemetry_body(
            event_id="evt-vscode-0001",
            client={"name": "vscode_extension", "version": "0.2.0", "platform": "darwin"},
        ),
        headers=auth_headers(TEST_VSCODE_TOKEN),
    )
    assert vscode_ok.status_code == 202


def test_unknown_route_before_auth() -> None:
    client, _ = _authed_client()
    assert client.get("/api/v1/missing").status_code == 404
