"""Slice 7.15 — end-to-end Community Cloud API pipeline verification.

Verification only: exercises the combined request pipeline for all six
production routes with realistic in-memory adapters. No product changes.
"""

from __future__ import annotations

import json

import pytest

from codestrata_platform.community_cloud_api.errors import (
    ERROR_AUTHENTICATION_REQUIRED,
    ERROR_AUTHENTICATION_UNAVAILABLE,
    ERROR_CLIENT_NOT_AUTHORIZED,
    ERROR_EVENT_IDENTITY_CONFLICT,
    ERROR_EVENT_IDENTITY_UNAVAILABLE,
    ERROR_RATE_LIMIT_EXCEEDED,
    ERROR_TELEMETRY_SINK_UNAVAILABLE,
)
from codestrata_platform.community_cloud_api.payload_limits import PayloadLimitPolicy

from .e2e_helpers import (
    INGESTION_ROUTES,
    auth_for,
    body_for,
    build_verification_harness,
    conflict_body_for,
    tight_rate_limit_policy,
)


@pytest.fixture()
def harness():
    return build_verification_harness()


def test_production_route_count_and_registry(harness) -> None:
    registry = harness.client.app.state.community_cloud_route_registry
    assert registry.diagnostics().registered_route_count == 6
    paths = {(r.method, r.path) for r in registry.list_routes()}
    assert paths == {
        ("GET", "/health"),
        ("POST", "/telemetry"),
        ("POST", "/assessment-metadata"),
        ("POST", "/cli-events"),
        ("POST", "/extension-events"),
        ("POST", "/ai-usage"),
    }
    assert harness.client.app.docs_url is None
    assert harness.client.app.openapi_url is None


def test_health_remains_public_and_deterministic(harness) -> None:
    first = harness.client.get("/api/v1/health")
    second = harness.client.get(
        "/api/v1/health", headers={"X-Request-Id": "health-probe-1"}
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.content == second.content
    body = first.json()
    assert body["status"] == "ok"
    assert body["schema_version"] == "1.0"
    assert body["api_version"] == "v1"
    assert "request_id" not in body
    assert first.headers["Cache-Control"] == "no-store"
    assert first.headers["X-Community-Cloud-API-Version"] == "v1"
    assert second.headers["X-Request-Id"] == "health-probe-1"
    assert harness.total_sink_events() == 0


@pytest.mark.parametrize(("path", "kind"), INGESTION_ROUTES)
def test_ingestion_requires_authentication(harness, path: str, kind: str) -> None:
    response = harness.client.post(path, json=body_for(kind, event_id=f"e2e-noauth-{kind}"))
    assert response.status_code == 401
    assert response.json()["error"]["code"] == ERROR_AUTHENTICATION_REQUIRED
    assert response.headers.get("WWW-Authenticate") == "Bearer"
    assert harness.sink_count(kind) == 0
    assert harness.identity_count() == 0


@pytest.mark.parametrize(("path", "kind"), INGESTION_ROUTES)
def test_happy_path_ingest_retry_conflict(harness, path: str, kind: str) -> None:
    event_id = f"e2e-happy-{kind}"
    headers = auth_for(kind, request_id=f"req-{kind}-1")
    first = harness.client.post(
        path, json=body_for(kind, event_id=event_id), headers=headers
    )
    assert first.status_code == 202, first.text
    assert first.json()["status"] == "accepted"
    assert "safe_event_reference" in first.json()
    assert first.headers["X-Community-Cloud-API-Version"] == "v1"
    assert first.headers.get("RateLimit-Limit") is not None
    assert first.headers.get("RateLimit-Remaining") is not None
    assert harness.sink_count(kind) == 1
    assert harness.identity_count() == 1

    # Exact retry: identity lookup short-circuits sink; recorder not re-run.
    second = harness.client.post(
        path,
        json=body_for(kind, event_id=event_id),
        headers=auth_for(kind, request_id=f"req-{kind}-2"),
    )
    assert second.status_code == 200
    assert second.json()["status"] == "already_accepted"
    assert second.json()["retry_status"] == "exact_retry"
    assert second.json()["safe_event_reference"] == first.json()["safe_event_reference"]
    assert harness.sink_count(kind) == 1
    assert harness.identity_count() == 1

    # Conflict: same identity, different fingerprint — no additional sink write.
    conflict_payload = conflict_body_for(kind)
    conflict_payload["event_id"] = event_id
    conflict = harness.client.post(path, json=conflict_payload, headers=auth_for(kind))
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == ERROR_EVENT_IDENTITY_CONFLICT
    assert event_id not in conflict.text
    assert harness.sink_count(kind) == 1
    assert harness.identity_count() == 1


def test_cross_endpoint_sink_isolation(harness) -> None:
    for path, kind in INGESTION_ROUTES:
        response = harness.client.post(
            path,
            json=body_for(kind, event_id=f"e2e-iso-{kind}"),
            headers=auth_for(kind),
        )
        assert response.status_code == 202, (kind, response.text)
    assert harness.sink_count("telemetry") == 1
    assert harness.sink_count("assessment_metadata") == 1
    assert harness.sink_count("cli_events") == 1
    assert harness.sink_count("extension_events") == 1
    assert harness.sink_count("ai_usage") == 1
    assert harness.identity_count() == 5
    assert harness.total_sink_events() == 5


def test_auth_precedes_rate_limiting() -> None:
    harness = build_verification_harness(
        rate_limit_policy=tight_rate_limit_policy(ingestion_limit=1, health_limit=10)
    )
    # Without credentials, auth fails before ingestion rate-limit capacity is consumed
    # as an authenticated scope (401). Auth-attempt limiting may still apply separately.
    missing = harness.client.post(
        "/api/v1/telemetry", json=body_for("telemetry", event_id="e2e-auth-first")
    )
    assert missing.status_code == 401
    assert missing.json()["error"]["code"] == ERROR_AUTHENTICATION_REQUIRED

    allowed = harness.client.post(
        "/api/v1/telemetry",
        json=body_for("telemetry", event_id="e2e-auth-first"),
        headers=auth_for("telemetry"),
    )
    assert allowed.status_code == 202
    limited = harness.client.post(
        "/api/v1/telemetry",
        json=body_for("telemetry", event_id="e2e-auth-second"),
        headers=auth_for("telemetry"),
    )
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == ERROR_RATE_LIMIT_EXCEEDED
    assert limited.headers.get("Retry-After") is not None
    assert harness.sink_count("telemetry") == 1


def test_rate_limiting_precedes_validation() -> None:
    harness = build_verification_harness(
        rate_limit_policy=tight_rate_limit_policy(ingestion_limit=1, health_limit=10)
    )
    assert (
        harness.client.post(
            "/api/v1/telemetry",
            json=body_for("telemetry", event_id="e2e-rl-valid"),
            headers=auth_for("telemetry"),
        ).status_code
        == 202
    )
    # Exhausted: invalid schema must still be 429, not 422.
    invalid = harness.client.post(
        "/api/v1/telemetry",
        json={"schema_version": "1.0"},
        headers=auth_for("telemetry"),
    )
    assert invalid.status_code == 429
    assert invalid.json()["error"]["code"] == ERROR_RATE_LIMIT_EXCEEDED


def test_validation_precedes_payload_limits() -> None:
    harness = build_verification_harness(
        payload_policy=PayloadLimitPolicy(
            max_request_bytes=80,
            max_json_depth=8,
            max_array_length=100,
            max_object_properties=100,
            max_string_length=4_096,
            max_traversal_count=10_000,
        )
    )
    # Tiny invalid body → schema/domain validation failure (not payload-size).
    invalid = harness.client.post(
        "/api/v1/telemetry",
        content=b'{"schema_version":"1.0"}',
        headers={
            **auth_for("telemetry"),
            "Content-Type": "application/json",
        },
    )
    assert invalid.status_code in {400, 422}
    assert invalid.status_code != 413
    assert "payload" not in invalid.json()["error"]["code"]

    # Valid schema but larger than max_request_bytes → payload limit after validation.
    oversized = harness.client.post(
        "/api/v1/telemetry",
        json=body_for("telemetry", event_id="e2e-payload-large"),
        headers=auth_for("telemetry"),
    )
    assert oversized.status_code == 413
    assert "payload" in oversized.json()["error"]["code"]
    assert harness.sink_count("telemetry") == 0
    assert harness.identity_count() == 0


def test_client_type_mismatch_after_validation(harness) -> None:
    # CLI token with vscode client payload → 403 after schema validation.
    response = harness.client.post(
        "/api/v1/telemetry",
        json=body_for(
            "telemetry",
            event_id="e2e-mismatch",
            client={
                "name": "vscode_extension",
                "version": "0.2.0",
                "platform": "darwin",
            },
        ),
        headers=auth_for("telemetry"),
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == ERROR_CLIENT_NOT_AUTHORIZED
    assert harness.sink_count("telemetry") == 0


def test_unavailable_verifier_fail_closed() -> None:
    harness = build_verification_harness(unavailable_verifier=True)
    assert harness.client.get("/api/v1/health").status_code == 200
    for path, kind in INGESTION_ROUTES:
        response = harness.client.post(
            path, json=body_for(kind, event_id=f"e2e-unver-{kind}"), headers=auth_for(kind)
        )
        assert response.status_code == 503
        assert response.json()["error"]["code"] == ERROR_AUTHENTICATION_UNAVAILABLE
        assert harness.sink_count(kind) == 0


def test_unavailable_identity_fail_closed_after_auth() -> None:
    harness = build_verification_harness(unavailable_identity=True)
    response = harness.client.post(
        "/api/v1/telemetry",
        json=body_for("telemetry", event_id="e2e-noid"),
        headers=auth_for("telemetry"),
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == ERROR_EVENT_IDENTITY_UNAVAILABLE
    assert harness.sink_count("telemetry") == 0


def test_unavailable_sink_fail_closed_no_identity_record() -> None:
    harness = build_verification_harness(unavailable_sinks=True)
    response = harness.client.post(
        "/api/v1/telemetry",
        json=body_for("telemetry", event_id="e2e-nosink"),
        headers=auth_for("telemetry"),
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == ERROR_TELEMETRY_SINK_UNAVAILABLE
    assert harness.identity_count() == 0


def test_unavailable_rate_limit_store_fail_closed() -> None:
    harness = build_verification_harness(unavailable_rate_limit_store=True)
    response = harness.client.post(
        "/api/v1/telemetry",
        json=body_for("telemetry", event_id="e2e-norl"),
        headers=auth_for("telemetry"),
    )
    assert response.status_code == 503
    assert harness.sink_count("telemetry") == 0


def test_logging_never_changes_behavior_or_leaks_secrets(harness) -> None:
    response = harness.client.post(
        "/api/v1/telemetry",
        json=body_for("telemetry", event_id="e2e-log-1"),
        headers=auth_for("telemetry"),
    )
    assert response.status_code == 202
    events = harness.log_sink.events()
    assert events  # logging occurred
    blob = json.dumps(events)
    assert "cscc_v1_" not in blob
    assert "e2e-log-1" not in blob
    assert "Authorization" not in blob
    # Same request shape without relying on logs still succeeds for another id.
    again = harness.client.post(
        "/api/v1/telemetry",
        json=body_for("telemetry", event_id="e2e-log-2"),
        headers=auth_for("telemetry"),
    )
    assert again.status_code == 202


def test_deterministic_accepted_response_shape(harness) -> None:
    a = harness.client.post(
        "/api/v1/cli-events",
        json=body_for("cli_events", event_id="e2e-det-1"),
        headers=auth_for("cli_events"),
    )
    b = harness.client.post(
        "/api/v1/cli-events",
        json=body_for("cli_events", event_id="e2e-det-1"),
        headers=auth_for("cli_events"),
    )
    assert a.status_code == 202
    assert b.status_code == 200
    assert list(a.json().keys()) == sorted(a.json().keys())
    assert list(b.json().keys()) == sorted(b.json().keys())
    assert set(a.json()) >= {"status", "safe_event_reference", "schema_version"}


def test_canonical_errors_sorted_keys(harness) -> None:
    response = harness.client.post(
        "/api/v1/ai-usage",
        json={"schema_version": "1.0"},
        headers=auth_for("ai_usage"),
    )
    assert response.status_code in {400, 422}
    envelope = response.json()
    assert "error" in envelope
    assert list(envelope.keys()) == sorted(envelope.keys())
    assert list(envelope["error"].keys()) == sorted(envelope["error"].keys())
