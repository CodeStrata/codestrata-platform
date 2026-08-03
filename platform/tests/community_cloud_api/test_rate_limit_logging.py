"""Rate-limit structured logging tests."""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

from codestrata_platform.community_cloud_api.logging.logger import (
    CommunityCloudLogger,
    MemoryLogSink,
    NullLogSink,
)
from codestrata_platform.community_cloud_api.app import create_community_cloud_app
from codestrata_platform.community_cloud_api.event_identity import InMemoryEventIdentityStore
from codestrata_platform.community_cloud_api.telemetry.ports import InMemoryTelemetryEventSink
from fastapi.testclient import TestClient

from .rate_limit_helpers import tight_rate_limit_policy
from .telemetry_helpers import valid_telemetry_body


def test_rate_limit_log_events_are_safe() -> None:
    identity = InMemoryEventIdentityStore()
    sink = InMemoryTelemetryEventSink()
    log_sink = MemoryLogSink()
    logger = CommunityCloudLogger.create(sink=log_sink)
    app = create_community_cloud_app(
        telemetry_sink=sink,
        event_identity_lookup=identity,
        event_identity_recorder=identity,
        logger=logger,
        rate_limit_policy=tight_rate_limit_policy(ingestion_limit=1),
            authentication_policy=disabled_authentication_policy(),
    )
    client = TestClient(app)
    assert client.post("/api/v1/telemetry", json=valid_telemetry_body()).status_code == 202
    assert (
        client.post(
            "/api/v1/telemetry", json=valid_telemetry_body(event_id="evt-2")
        ).status_code
        == 429
    )
    events = log_sink.events()
    types = {item["event_type"] for item in events}
    assert "rate_limit_allowed" in types
    assert "rate_limit_exceeded" in types
    for item in events:
        if item["event_type"].startswith("rate_limit_"):
            assert "client_host" not in item
            blob = str(item)
            assert "X-Forwarded-For" not in blob
            assert "event_id" not in item
            assert "installation_id" not in item
            assert item.get("rate_limit_policy_id") == "community-rate-limit-policy"
            assert "route_name" in item or item.get("route")


def test_broken_logger_does_not_fail_requests() -> None:
    class BrokenSink:
        def write(self, line: str) -> None:
            raise RuntimeError("boom")

    identity = InMemoryEventIdentityStore()
    sink = InMemoryTelemetryEventSink()
    logger = CommunityCloudLogger.create(sink=BrokenSink())  # type: ignore[arg-type]
    app = create_community_cloud_app(
        telemetry_sink=sink,
        event_identity_lookup=identity,
        event_identity_recorder=identity,
        logger=logger,
        rate_limit_policy=tight_rate_limit_policy(ingestion_limit=5),
            authentication_policy=disabled_authentication_policy(),
    )
    client = TestClient(app)
    assert client.post("/api/v1/telemetry", json=valid_telemetry_body()).status_code == 202
    _ = NullLogSink()
