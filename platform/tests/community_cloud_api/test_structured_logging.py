"""Structured logging foundation tests (Slice 7.5)."""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

import json

from fastapi.testclient import TestClient

from codestrata_platform.community_cloud_api import (
    COMMUNITY_LOGGING_POLICY_URN,
    CommunityCloudLogger,
    CommunityLoggingPolicy,
    PayloadLimitPolicy,
    create_community_cloud_app,
)
from codestrata_platform.community_cloud_api.logging import (
    LogEventType,
    MemoryLogSink,
    SequenceClock,
    SequenceRequestIdFactory,
    format_log_event,
)
from codestrata_platform.community_cloud_api.logging.models import (
    LogLevel,
    StructuredLogEvent,
)
from codestrata_platform.community_cloud_api.logging.sanitization import (
    redact_header_value,
    sanitize_request_id,
)

from .conftest import VALID_BODY, build_validation_test_registry


def _logger() -> tuple[CommunityCloudLogger, MemoryLogSink]:
    sink = MemoryLogSink()
    logger = CommunityCloudLogger.create(
        sink=sink,
        clock_ms=SequenceClock(start_ms=1000, step_ms=5),
        request_id_factory=SequenceRequestIdFactory(prefix="log"),
    )
    return logger, sink


def _app_client(
    *,
    logger: CommunityCloudLogger | None = None,
    payload_policy: PayloadLimitPolicy | None = None,
) -> tuple[TestClient, MemoryLogSink, CommunityCloudLogger]:
    if logger is None:
        logger, sink = _logger()
    else:
        sink = logger.sink  # type: ignore[assignment]
        assert isinstance(sink, MemoryLogSink)
    app = create_community_cloud_app(
        registry=build_validation_test_registry(),
        payload_policy=payload_policy,
        logger=logger,
            authentication_policy=disabled_authentication_policy(),
    )
    return TestClient(app), sink, logger


def test_policy_version() -> None:
    policy = CommunityLoggingPolicy.default()
    assert policy.policy_version == COMMUNITY_LOGGING_POLICY_URN
    assert policy.policy_version == "community-logging-policy:1.0"
    assert "request_received" in policy.allowed_event_types


def test_structured_json_sorted_keys_no_default_timestamp() -> None:
    event = StructuredLogEvent(
        event_type=LogEventType.REQUEST_RECEIVED,
        level=LogLevel.INFO,
        api_version="v1",
        method="GET",
        route="/api/v1/health",
        request_id="log-00000001",
        event_seq=1,
    )
    line = format_log_event(event)
    payload = json.loads(line)
    assert list(payload.keys()) == sorted(payload.keys())
    assert "timestamp" not in payload
    assert payload["event_type"] == "request_received"


def test_health_logging_sequence() -> None:
    logger, sink = _logger()
    client = TestClient(create_community_cloud_app(logger=logger,
        authentication_policy=disabled_authentication_policy(),
    ))
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "request_id" not in response.json()
    types = [item["event_type"] for item in sink.events()]
    assert types == [
        "request_received",
        "rate_limit_allowed",
        "health_checked",
        "request_completed",
    ]
    assert all(item["route"] == "/api/v1/health" for item in sink.events())
    assert all("timestamp" not in item for item in sink.events())


def test_validation_failed_logging() -> None:
    client, sink, _ = _app_client()
    response = client.post("/api/v1/_test/validation-envelope", json={"client_name": "c"})
    assert response.status_code == 422
    types = [item["event_type"] for item in sink.events()]
    assert "request_received" in types
    assert "validation_failed" in types
    assert "request_failed" in types
    assert "body" not in json.dumps(sink.events())
    assert "payload" not in json.dumps(sink.events())


def test_payload_rejected_logging() -> None:
    policy = PayloadLimitPolicy(
        max_request_bytes=40,
        max_json_depth=8,
        max_array_length=100,
        max_object_properties=100,
        max_string_length=4096,
        max_traversal_count=10000,
    )
    client, sink, _ = _app_client(payload_policy=policy)
    response = client.post("/api/v1/_test/validation-envelope", json=VALID_BODY)
    assert response.status_code == 413
    types = [item["event_type"] for item in sink.events()]
    assert "payload_rejected" in types
    assert "request_failed" in types
    assert VALID_BODY["event_type"] not in json.dumps(sink.events())


def test_request_completion_for_valid_post() -> None:
    client, sink, _ = _app_client()
    response = client.post("/api/v1/_test/validation-envelope", json=VALID_BODY)
    assert response.status_code == 200
    types = [item["event_type"] for item in sink.events()]
    assert types[0] == "request_received"
    assert types[-1] == "request_completed"
    completed = sink.events()[-1]
    assert completed["status_code"] == 200
    assert "duration_ms" in completed


def test_redaction_helpers() -> None:
    assert redact_header_value("Authorization", "Bearer abc.def.ghi") == "[redacted]"
    assert redact_header_value("Cookie", "session=1") == "[redacted]"
    assert sanitize_request_id("ok-id-1", max_length=64) == "ok-id-1"
    assert sanitize_request_id("Bearer supersecrettoken", max_length=64) is None
    assert sanitize_request_id("/Users/satish/secret", max_length=64) is None


def test_logging_failure_does_not_break_request() -> None:
    class BoomSink:
        def write(self, line: str) -> None:
            raise RuntimeError("sink broken")

    logger = CommunityCloudLogger.create(
        sink=BoomSink(),  # type: ignore[arg-type]
        clock_ms=SequenceClock(),
        request_id_factory=SequenceRequestIdFactory(),
    )
    client = TestClient(create_community_cloud_app(logger=logger,
        authentication_policy=disabled_authentication_policy(),
    ))
    assert client.get("/api/v1/health").status_code == 200


def test_auto_request_id_not_in_response_body() -> None:
    logger, sink = _logger()
    client = TestClient(create_community_cloud_app(logger=logger,
        authentication_policy=disabled_authentication_policy(),
    ))
    response = client.get("/api/v1/missing")
    assert response.status_code == 404
    body = response.json()
    assert "request_id" not in body.get("error", {})
    assert sink.events()[0]["request_id"].startswith("log-")


def test_client_request_id_used_in_logs_and_header_echo() -> None:
    logger, sink = _logger()
    client = TestClient(create_community_cloud_app(logger=logger,
        authentication_policy=disabled_authentication_policy(),
    ))
    response = client.get(
        "/api/v1/health",
        headers={"X-Request-Id": "client-fixed-1"},
    )
    assert response.status_code == 200
    assert response.headers["X-Request-Id"] == "client-fixed-1"
    assert "request_id" not in response.json()
    assert all(item["request_id"] == "client-fixed-1" for item in sink.events())


def test_determinism_same_inputs_same_log_shape() -> None:
    def run() -> list[dict[str, object]]:
        logger, sink = _logger()
        client = TestClient(create_community_cloud_app(logger=logger,
        authentication_policy=disabled_authentication_policy(),
    ))
        client.get("/api/v1/health")
        return sink.events()

    assert run() == run()


def test_no_secret_fields_in_log_events() -> None:
    client, sink, _ = _app_client()
    client.post(
        "/api/v1/_test/validation-envelope",
        json=VALID_BODY,
        headers={"Authorization": "Bearer supersecrettokenvalue"},
    )
    blob = json.dumps(sink.events())
    assert "Bearer" not in blob
    assert "supersecrettokenvalue" not in blob
    assert "Authorization" not in blob
