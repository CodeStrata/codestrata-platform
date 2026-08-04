"""Verification app factory wiring."""

from __future__ import annotations

from verification.community_cloud_api.app_factory import build_verification_app
from verification.community_cloud_api.contract import TEST_CLI_TOKEN


def test_build_verification_app_enables_auth() -> None:
    app = build_verification_app()
    response = app.client.post("/api/v1/telemetry", json={"schema_version": "1.0"})
    assert response.status_code == 401
    assert TEST_CLI_TOKEN not in response.text


def test_sinks_start_empty() -> None:
    app = build_verification_app()
    assert app.total_sink_events() == 0
    assert app.identity_count() == 0
