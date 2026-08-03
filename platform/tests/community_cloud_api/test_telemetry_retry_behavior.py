"""Telemetry retry / identity behavior tests."""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

from codestrata_platform.community_cloud_api.app import create_community_cloud_app
from codestrata_platform.community_cloud_api.errors import (
    ERROR_EVENT_IDENTITY_CONFLICT,
    ERROR_EVENT_IDENTITY_RECORD_FAILED,
    ERROR_EVENT_IDENTITY_UNAVAILABLE,
    ERROR_TELEMETRY_REJECTED,
    ERROR_TELEMETRY_SINK_UNAVAILABLE,
)
from codestrata_platform.community_cloud_api.event_identity import (
    EventIdentityScope,
    InMemoryEventIdentityStore,
    build_event_key,
    compute_payload_fingerprint,
)
from codestrata_platform.community_cloud_api.telemetry.models import TelemetryIngestionRequest
from codestrata_platform.community_cloud_api.telemetry.ports import InMemoryTelemetryEventSink
from fastapi.testclient import TestClient

from .telemetry_helpers import configured_client, valid_telemetry_body


def test_exact_retry_short_circuits_sink() -> None:
    client, sink, _, log_sink = configured_client()
    first = client.post("/api/v1/telemetry", json=valid_telemetry_body())
    assert first.status_code == 202
    ref = first.json()["safe_event_reference"]
    second = client.post("/api/v1/telemetry", json=valid_telemetry_body())
    assert second.status_code == 200
    assert second.json()["status"] == "already_accepted"
    assert second.json()["retry_status"] == "exact_retry"
    assert second.json()["safe_event_reference"] == ref
    assert len(sink.events) == 1
    events = log_sink.events()
    assert any(item.get("event_type") == "telemetry_retry" for item in events)
    assert all("event_id" not in item for item in events)
    assert all("payload_fingerprint" not in item for item in events)
    assert all("installation_id" not in item for item in events)


def test_conflicting_retry_409() -> None:
    client, sink, _, _ = configured_client()
    assert client.post("/api/v1/telemetry", json=valid_telemetry_body()).status_code == 202
    conflict = client.post(
        "/api/v1/telemetry",
        json=valid_telemetry_body(
            properties={"feature": "other", "outcome": "failed"},
        ),
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == ERROR_EVENT_IDENTITY_CONFLICT
    assert "evt-test-0001" not in conflict.text
    assert "fp:" not in conflict.text
    assert len(sink.events) == 1


def test_scope_distinguishes_client_type_event_type_installation() -> None:
    client, sink, _, _ = configured_client()
    assert client.post("/api/v1/telemetry", json=valid_telemetry_body()).status_code == 202
    other_client = valid_telemetry_body()
    other_client["client"] = {
        "name": "vscode_extension",
        "version": "0.2.0",
        "platform": "darwin",
    }
    assert client.post("/api/v1/telemetry", json=other_client).status_code == 202
    other_type = valid_telemetry_body(event_type="feature_invoked")
    assert client.post("/api/v1/telemetry", json=other_type).status_code == 202
    with_install = valid_telemetry_body(installation_id="install-abcdef12")
    assert client.post("/api/v1/telemetry", json=with_install).status_code == 202
    assert len(sink.events) == 4


def test_fingerprint_includes_event_id_and_occurred_at() -> None:
    model = TelemetryIngestionRequest.model_validate(valid_telemetry_body())
    fp1 = compute_payload_fingerprint(model.fingerprint_payload())
    model2 = TelemetryIngestionRequest.model_validate(
        valid_telemetry_body(event_id="evt-test-0002")
    )
    fp2 = compute_payload_fingerprint(model2.fingerprint_payload())
    assert fp1 != fp2
    with_time = TelemetryIngestionRequest.model_validate(
        valid_telemetry_body(occurred_at="2026-07-29T18:00:00Z")
    )
    assert compute_payload_fingerprint(with_time.fingerprint_payload()) != fp1
    # request_id never on model → excluded from fingerprint material by absence.
    assert "request_id" not in model.fingerprint_payload()


def test_event_key_stable() -> None:
    scope = EventIdentityScope(
        api_version="v1",
        client_type="codestrata_cli",
        event_type="application_started",
        event_id="evt-test-0001",
    )
    assert build_event_key(scope) == build_event_key(scope)


def test_lookup_unavailable_fail_closed() -> None:
    sink = InMemoryTelemetryEventSink()
    client = TestClient(create_community_cloud_app(telemetry_sink=sink,
        authentication_policy=disabled_authentication_policy(),
    ))
    response = client.post("/api/v1/telemetry", json=valid_telemetry_body())
    assert response.status_code == 503
    assert response.json()["error"]["code"] == ERROR_EVENT_IDENTITY_UNAVAILABLE
    assert sink.events == []


def test_rejected_sink() -> None:
    store = InMemoryEventIdentityStore()
    sink = InMemoryTelemetryEventSink()
    sink.reject_next = True
    client = TestClient(
        create_community_cloud_app(
            telemetry_sink=sink,
            event_identity_lookup=store,
            event_identity_recorder=store,
                authentication_policy=disabled_authentication_policy(),
    )
    )
    response = client.post("/api/v1/telemetry", json=valid_telemetry_body())
    assert response.status_code == 422
    assert response.json()["error"]["code"] == ERROR_TELEMETRY_REJECTED
    assert store._items == {}  # noqa: SLF001


def test_sink_exception_sanitized() -> None:
    store = InMemoryEventIdentityStore()
    sink = InMemoryTelemetryEventSink()
    sink.fail_next = True
    client = TestClient(
        create_community_cloud_app(
            telemetry_sink=sink,
            event_identity_lookup=store,
            event_identity_recorder=store,
                authentication_policy=disabled_authentication_policy(),
    )
    )
    response = client.post("/api/v1/telemetry", json=valid_telemetry_body())
    assert response.status_code == 503
    assert response.json()["error"]["code"] == ERROR_TELEMETRY_SINK_UNAVAILABLE
    assert "simulated_sink_failure" not in response.text


def test_recorder_failure_after_sink_acceptance() -> None:
    class BoomRecorder:
        def record(self, identity: object) -> None:
            raise RuntimeError("recorder_boom")

    store = InMemoryEventIdentityStore()
    sink = InMemoryTelemetryEventSink()
    client = TestClient(
        create_community_cloud_app(
            telemetry_sink=sink,
            event_identity_lookup=store,
            event_identity_recorder=BoomRecorder(),
                authentication_policy=disabled_authentication_policy(),
    )
    )
    response = client.post("/api/v1/telemetry", json=valid_telemetry_body())
    assert response.status_code == 503
    assert response.json()["error"]["code"] == ERROR_EVENT_IDENTITY_RECORD_FAILED
    assert len(sink.events) == 1
    assert "recorder_boom" not in response.text
    assert "exactly-once" not in response.text.lower()
