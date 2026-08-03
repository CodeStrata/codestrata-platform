"""End-to-end rate-limit pipeline and endpoint behavior."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.errors import (
    ERROR_METHOD_NOT_ALLOWED,
    ERROR_NOT_FOUND,
    ERROR_RATE_LIMIT_EXCEEDED,
    ERROR_RATE_LIMIT_UNAVAILABLE,
)
from codestrata_platform.community_cloud_api.logging.context import SequenceClock
from codestrata_platform.community_cloud_api.rate_limiting.responses import (
    HEADER_RATE_LIMIT_LIMIT,
    HEADER_RATE_LIMIT_REMAINING,
    HEADER_RATE_LIMIT_RESET,
    HEADER_RETRY_AFTER,
)

from .rate_limit_helpers import rate_limited_client, tight_rate_limit_policy
from .telemetry_helpers import valid_telemetry_body


def test_unknown_route_404_without_consuming_limit() -> None:
    client, sink, *_ = rate_limited_client(policy=tight_rate_limit_policy(ingestion_limit=1))
    missing = client.get("/api/v1/does-not-exist")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == ERROR_NOT_FOUND
    # Still able to ingest once — unknown route did not consume ingestion bucket.
    ok = client.post("/api/v1/telemetry", json=valid_telemetry_body())
    assert ok.status_code == 202
    assert len(sink.events) == 1


def test_unsupported_method_before_rate_limit() -> None:
    client, *_ = rate_limited_client(policy=tight_rate_limit_policy(health_limit=1))
    # POST /health is 405 — must not consume health GET bucket.
    rejected = client.post("/api/v1/health")
    assert rejected.status_code == 405
    assert rejected.json()["error"]["code"] == ERROR_METHOD_NOT_ALLOWED
    ok = client.get("/api/v1/health")
    assert ok.status_code == 200
    limited = client.get("/api/v1/health")
    assert limited.status_code == 429


def test_rate_limit_before_validation_and_handler() -> None:
    client, sink, identity, *_ = rate_limited_client(
        policy=tight_rate_limit_policy(ingestion_limit=1)
    )
    assert client.post("/api/v1/telemetry", json=valid_telemetry_body()).status_code == 202
    # Malformed body would normally be 400 — when limited, return 429 without sink/identity.
    limited = client.post(
        "/api/v1/telemetry",
        content=b"{",
        headers={"Content-Type": "application/json"},
    )
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == ERROR_RATE_LIMIT_EXCEEDED
    assert limited.json()["error"]["message"] == "Request rate limit exceeded."
    assert limited.headers.get(HEADER_RETRY_AFTER) is not None
    assert limited.headers.get(HEADER_RATE_LIMIT_LIMIT) == "1"
    assert limited.headers.get(HEADER_RATE_LIMIT_REMAINING) == "0"
    assert limited.headers.get(HEADER_RATE_LIMIT_RESET) is not None
    body = limited.json()
    assert "rate-scope" not in str(body)
    assert "203." not in str(body)
    assert len(sink.events) == 1
    assert len(identity._items) == 1  # noqa: SLF001


def test_request_id_and_event_id_do_not_bypass() -> None:
    client, sink, *_ = rate_limited_client(policy=tight_rate_limit_policy(ingestion_limit=1))
    assert (
        client.post(
            "/api/v1/telemetry",
            json=valid_telemetry_body(event_id="evt-bypass-0001"),
            headers={"X-Request-Id": "req-1"},
        ).status_code
        == 202
    )
    limited = client.post(
        "/api/v1/telemetry",
        json=valid_telemetry_body(event_id="evt-bypass-0002"),
        headers={"X-Request-Id": "req-2"},
    )
    assert limited.status_code == 429
    assert len(sink.events) == 1


def test_exact_retry_still_consumes_capacity() -> None:
    client, sink, *_ = rate_limited_client(policy=tight_rate_limit_policy(ingestion_limit=2))
    body = valid_telemetry_body(event_id="evt-retry-same")
    assert client.post("/api/v1/telemetry", json=body).status_code == 202
    retry = client.post("/api/v1/telemetry", json=body)
    assert retry.status_code == 200  # exact retry accepted
    assert len(sink.events) == 1
    limited = client.post("/api/v1/telemetry", json=valid_telemetry_body(event_id="evt-new"))
    assert limited.status_code == 429


def test_forwarded_headers_do_not_alter_scope() -> None:
    client, sink, *_ = rate_limited_client(policy=tight_rate_limit_policy(ingestion_limit=1))
    assert client.post("/api/v1/telemetry", json=valid_telemetry_body()).status_code == 202
    spoofed = client.post(
        "/api/v1/telemetry",
        json=valid_telemetry_body(event_id="evt-spoof"),
        headers={
            "X-Forwarded-For": "198.51.100.1",
            "X-Real-IP": "198.51.100.2",
            "CF-Connecting-IP": "198.51.100.3",
            "Forwarded": "for=198.51.100.4",
        },
    )
    assert spoofed.status_code == 429
    assert len(sink.events) == 1


def test_health_allowed_then_429() -> None:
    client, *_ = rate_limited_client(policy=tight_rate_limit_policy(health_limit=1))
    first = client.get("/api/v1/health")
    assert first.status_code == 200
    assert first.json()["status"] == "ok"
    assert first.headers.get(HEADER_RATE_LIMIT_LIMIT) == "1"
    assert first.headers.get(HEADER_RATE_LIMIT_REMAINING) == "0"
    second = client.get("/api/v1/health")
    assert second.status_code == 429
    assert second.json()["error"]["code"] == ERROR_RATE_LIMIT_EXCEEDED


def test_ingestion_endpoints_protected() -> None:
    paths = (
        "/api/v1/telemetry",
        "/api/v1/assessment-metadata",
        "/api/v1/cli-events",
        "/api/v1/extension-events",
        "/api/v1/ai-usage",
    )
    # Each path uses the shared ingestion group — one budget for all ingestion routes.
    client, sink, *_ = rate_limited_client(policy=tight_rate_limit_policy(ingestion_limit=1))
    assert client.post("/api/v1/telemetry", json=valid_telemetry_body()).status_code == 202
    for path in paths[1:]:
        # Bodies are intentionally invalid/minimal — limited before validation.
        response = client.post(path, json={"schema_version": "1.0"})
        assert response.status_code == 429, path
    assert len(sink.events) == 1


def test_unavailable_store_fail_closed_ingestion_health_fallback() -> None:
    client, sink, *_ = rate_limited_client(
        policy=tight_rate_limit_policy(health_limit=2, ingestion_limit=2),
        unavailable_store=True,
        clock=SequenceClock(start_ms=0, step_ms=0),
    )
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    blocked = client.post("/api/v1/telemetry", json=valid_telemetry_body())
    assert blocked.status_code == 503
    assert blocked.json()["error"]["code"] == ERROR_RATE_LIMIT_UNAVAILABLE
    assert len(sink.events) == 0


def test_disabled_policy_skips_limiting() -> None:
    client, sink, *_ = rate_limited_client(
        policy=tight_rate_limit_policy(ingestion_limit=1, enabled=False)
    )
    for idx in range(3):
        response = client.post(
            "/api/v1/telemetry",
            json=valid_telemetry_body(event_id=f"evt-disabled-{idx}"),
        )
        assert response.status_code == 202
    assert len(sink.events) == 3
