"""AI usage retry / identity tests."""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

from codestrata_platform.community_cloud_api.ai_usage.enums import AI_USAGE_SOURCE_TYPE
from codestrata_platform.community_cloud_api.ai_usage.models import AiUsageRequest
from codestrata_platform.community_cloud_api.ai_usage.ports import InMemoryAiUsageSink
from codestrata_platform.community_cloud_api.app import create_community_cloud_app
from codestrata_platform.community_cloud_api.errors import (
    ERROR_AI_USAGE_RECORD_FAILED,
    ERROR_AI_USAGE_REJECTED,
    ERROR_AI_USAGE_SINK_UNAVAILABLE,
    ERROR_EVENT_IDENTITY_CONFLICT,
)
from codestrata_platform.community_cloud_api.event_identity import (
    EventIdentityScope,
    InMemoryEventIdentityStore,
    build_event_key,
    compute_payload_fingerprint,
)
from fastapi.testclient import TestClient

from .ai_usage_helpers import configured_ai_usage_client, valid_ai_usage_body


def test_exact_retry_and_conflict() -> None:
    client, sink, _, log_sink, *_ = configured_ai_usage_client()
    first = client.post("/api/v1/ai-usage", json=valid_ai_usage_body())
    assert first.status_code == 202
    ref = first.json()["safe_event_reference"]
    second = client.post("/api/v1/ai-usage", json=valid_ai_usage_body())
    assert second.status_code == 200
    assert second.json()["status"] == "already_accepted"
    assert second.json()["safe_event_reference"] == ref
    assert len(sink.events) == 1
    assert any(e.get("event_type") == "ai_usage_retry" for e in log_sink.events())
    assert all("event_id" not in e for e in log_sink.events())
    assert all("prompt" not in e for e in log_sink.events())

    conflict = valid_ai_usage_body()
    conflict["usage"] = {**conflict["usage"], "provider_family": "aws_bedrock"}  # type: ignore[dict-item]
    response = client.post("/api/v1/ai-usage", json=conflict)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == ERROR_EVENT_IDENTITY_CONFLICT
    assert "aws_bedrock" not in response.text
    assert len(sink.events) == 1


def test_fingerprint_and_scope_distinct_from_cli() -> None:
    model = AiUsageRequest.model_validate(valid_ai_usage_body())
    fp1 = compute_payload_fingerprint(model.fingerprint_payload())
    other = valid_ai_usage_body()
    other["usage"] = {**other["usage"], "outcome": "failed", "failure_category": "timeout"}  # type: ignore[dict-item]
    model2 = AiUsageRequest.model_validate(other)
    assert compute_payload_fingerprint(model2.fingerprint_payload()) != fp1

    ai_scope = EventIdentityScope(
        api_version="v1",
        client_type="codestrata_cli",
        event_type=AI_USAGE_SOURCE_TYPE,
        event_id="shared-id-0001",
    )
    cli_scope = EventIdentityScope(
        api_version="v1",
        client_type="codestrata_cli",
        event_type="cli_event_submitted",
        event_id="shared-id-0001",
    )
    assert build_event_key(ai_scope) != build_event_key(cli_scope)


def test_sink_recorder_failures() -> None:
    store = InMemoryEventIdentityStore()
    sink = InMemoryAiUsageSink()
    sink.reject_next = True
    client = TestClient(
        create_community_cloud_app(
            ai_usage_sink=sink,
            event_identity_lookup=store,
            event_identity_recorder=store,
                authentication_policy=disabled_authentication_policy(),
    )
    )
    rejected = client.post("/api/v1/ai-usage", json=valid_ai_usage_body())
    assert rejected.json()["error"]["code"] == ERROR_AI_USAGE_REJECTED

    sink2 = InMemoryAiUsageSink()
    sink2.fail_next = True
    client2 = TestClient(
        create_community_cloud_app(
            ai_usage_sink=sink2,
            event_identity_lookup=store,
            event_identity_recorder=store,
                authentication_policy=disabled_authentication_policy(),
    )
    )
    boom = client2.post(
        "/api/v1/ai-usage", json=valid_ai_usage_body(event_id="ai-usage-fail01")
    )
    assert boom.json()["error"]["code"] == ERROR_AI_USAGE_SINK_UNAVAILABLE
    assert "simulated_ai_usage_sink_failure" not in boom.text

    class BoomRecorder:
        def record(self, identity: object) -> None:
            raise RuntimeError("recorder_boom")

    sink3 = InMemoryAiUsageSink()
    client3 = TestClient(
        create_community_cloud_app(
            ai_usage_sink=sink3,
            event_identity_lookup=InMemoryEventIdentityStore(),
            event_identity_recorder=BoomRecorder(),
                authentication_policy=disabled_authentication_policy(),
    )
    )
    rec = client3.post(
        "/api/v1/ai-usage", json=valid_ai_usage_body(event_id="ai-usage-rec001")
    )
    assert rec.json()["error"]["code"] == ERROR_AI_USAGE_RECORD_FAILED
    assert len(sink3.events) == 1
