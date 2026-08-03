"""Authentication + rate-limit integration tests."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.app import create_community_cloud_app
from codestrata_platform.community_cloud_api.event_identity import InMemoryEventIdentityStore
from codestrata_platform.community_cloud_api.logging.context import SequenceClock
from codestrata_platform.community_cloud_api.rate_limiting import InMemoryRateLimitStore
from codestrata_platform.community_cloud_api.telemetry.ports import InMemoryTelemetryEventSink
from fastapi.testclient import TestClient

from .auth_test_support import TEST_CLI_TOKEN, auth_headers, build_test_verifier
from .rate_limit_helpers import tight_rate_limit_policy
from .telemetry_helpers import valid_telemetry_body


def test_authenticated_scope_ignores_request_id_and_ip_spoofing() -> None:
    sink = InMemoryTelemetryEventSink()
    store = InMemoryEventIdentityStore()
    rl_store = InMemoryRateLimitStore()
    app = create_community_cloud_app(
        telemetry_sink=sink,
        event_identity_lookup=store,
        event_identity_recorder=store,
        credential_verifier=build_test_verifier(),
        rate_limit_policy=tight_rate_limit_policy(ingestion_limit=1),
        rate_limit_store=rl_store,
        rate_limit_clock_ms=SequenceClock(start_ms=0, step_ms=0),
    )
    client = TestClient(app)
    first = client.post(
        "/api/v1/telemetry",
        json=valid_telemetry_body(event_id="evt-auth-rl-1"),
        headers={**auth_headers(TEST_CLI_TOKEN), "X-Request-Id": "req-a"},
    )
    assert first.status_code == 202
    second = client.post(
        "/api/v1/telemetry",
        json=valid_telemetry_body(event_id="evt-auth-rl-2"),
        headers={
            **auth_headers(TEST_CLI_TOKEN),
            "X-Request-Id": "req-b",
            "X-Forwarded-For": "198.51.100.9",
        },
    )
    assert second.status_code == 429
    assert len(sink.events) == 1
    for key in rl_store.key_snapshot():
        assert "cscc_v1_" not in key
        assert TEST_CLI_TOKEN not in key
