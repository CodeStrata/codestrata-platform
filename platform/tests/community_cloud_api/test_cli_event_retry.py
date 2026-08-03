"""CLI event retry / identity tests."""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

from codestrata_platform.community_cloud_api.app import create_community_cloud_app
from codestrata_platform.community_cloud_api.cli_events.enums import CLI_EVENT_SOURCE_TYPE
from codestrata_platform.community_cloud_api.cli_events.models import CliEventRequest
from codestrata_platform.community_cloud_api.cli_events.ports import InMemoryCliEventSink
from codestrata_platform.community_cloud_api.errors import (
    ERROR_CLI_EVENT_RECORD_FAILED,
    ERROR_CLI_EVENT_REJECTED,
    ERROR_CLI_EVENT_SINK_UNAVAILABLE,
    ERROR_EVENT_IDENTITY_CONFLICT,
)
from codestrata_platform.community_cloud_api.event_identity import (
    EventIdentityScope,
    InMemoryEventIdentityStore,
    build_event_key,
    compute_payload_fingerprint,
)
from fastapi.testclient import TestClient

from .cli_event_helpers import configured_cli_client, valid_cli_event_body


def test_exact_retry_and_conflict() -> None:
    client, sink, _, log_sink, _, _ = configured_cli_client()
    first = client.post("/api/v1/cli-events", json=valid_cli_event_body())
    assert first.status_code == 202
    ref = first.json()["safe_event_reference"]
    second = client.post("/api/v1/cli-events", json=valid_cli_event_body())
    assert second.status_code == 200
    assert second.json()["status"] == "already_accepted"
    assert second.json()["safe_event_reference"] == ref
    assert len(sink.events) == 1
    assert any(e.get("event_type") == "cli_event_retry" for e in log_sink.events())
    assert all("event_id" not in e for e in log_sink.events())

    conflict = valid_cli_event_body()
    conflict["event"] = {**conflict["event"], "operation": "doctor"}  # type: ignore[dict-item]
    response = client.post("/api/v1/cli-events", json=conflict)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == ERROR_EVENT_IDENTITY_CONFLICT
    assert "doctor" not in response.text
    assert len(sink.events) == 1


def test_operation_affects_fingerprint_not_scope_event_type() -> None:
    model = CliEventRequest.model_validate(valid_cli_event_body())
    fp1 = compute_payload_fingerprint(model.fingerprint_payload())
    other = valid_cli_event_body()
    other["event"] = {**other["event"], "operation": "scan"}  # type: ignore[dict-item]
    model2 = CliEventRequest.model_validate(other)
    assert compute_payload_fingerprint(model2.fingerprint_payload()) != fp1
    scope = EventIdentityScope(
        api_version="v1",
        client_type="codestrata_cli",
        event_type=CLI_EVENT_SOURCE_TYPE,
        event_id="cli-evt-0001",
    )
    assert build_event_key(scope) == build_event_key(scope)


def test_sink_recorder_failures() -> None:
    store = InMemoryEventIdentityStore()
    sink = InMemoryCliEventSink()
    sink.reject_next = True
    client = TestClient(
        create_community_cloud_app(
            cli_event_sink=sink,
            event_identity_lookup=store,
            event_identity_recorder=store,
                authentication_policy=disabled_authentication_policy(),
    )
    )
    rejected = client.post("/api/v1/cli-events", json=valid_cli_event_body())
    assert rejected.json()["error"]["code"] == ERROR_CLI_EVENT_REJECTED

    sink2 = InMemoryCliEventSink()
    sink2.fail_next = True
    client2 = TestClient(
        create_community_cloud_app(
            cli_event_sink=sink2,
            event_identity_lookup=store,
            event_identity_recorder=store,
                authentication_policy=disabled_authentication_policy(),
    )
    )
    boom = client2.post(
        "/api/v1/cli-events", json=valid_cli_event_body(event_id="cli-evt-fail01")
    )
    assert boom.json()["error"]["code"] == ERROR_CLI_EVENT_SINK_UNAVAILABLE
    assert "simulated_cli_sink_failure" not in boom.text

    class BoomRecorder:
        def record(self, identity: object) -> None:
            raise RuntimeError("recorder_boom")

    sink3 = InMemoryCliEventSink()
    client3 = TestClient(
        create_community_cloud_app(
            cli_event_sink=sink3,
            event_identity_lookup=InMemoryEventIdentityStore(),
            event_identity_recorder=BoomRecorder(),
                authentication_policy=disabled_authentication_policy(),
    )
    )
    rec = client3.post(
        "/api/v1/cli-events", json=valid_cli_event_body(event_id="cli-evt-rec001")
    )
    assert rec.json()["error"]["code"] == ERROR_CLI_EVENT_RECORD_FAILED
    assert len(sink3.events) == 1
