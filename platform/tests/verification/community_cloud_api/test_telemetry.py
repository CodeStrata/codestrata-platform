"""Telemetry endpoint verification."""

from __future__ import annotations

from verification.community_cloud_api.contract import INGESTION_PATHS
from verification.community_cloud_api.credentials import auth_headers
from verification.community_cloud_api.requests import body_for


def test_telemetry_accept(verification_app) -> None:
    response = verification_app.client.post(
        INGESTION_PATHS["telemetry"],
        json=body_for("telemetry", event_id="sv7-unit-tel"),
        headers=auth_headers(),
    )
    assert response.status_code == 202
    assert verification_app.sink_count("telemetry") == 1
    assert verification_app.sink_count("assessment_metadata") == 0
    assert verification_app.sink_count("cli_events") == 0
    assert verification_app.sink_count("extension_events") == 0
    assert verification_app.sink_count("ai_usage") == 0
