"""AI usage endpoint verification."""

from __future__ import annotations

from verification.community_cloud_api.contract import INGESTION_PATHS
from verification.community_cloud_api.credentials import auth_headers
from verification.community_cloud_api.requests import body_for


def test_ai_usage_accept(verification_app) -> None:
    response = verification_app.client.post(
        INGESTION_PATHS["ai_usage"],
        json=body_for("ai_usage", event_id="sv7-unit-ai"),
        headers=auth_headers(),
    )
    assert response.status_code == 202
    assert verification_app.sink_count("ai_usage") == 1
    assert verification_app.sink_count("telemetry") == 0
    usage = body_for("ai_usage")["usage"]
    assert usage["capability"] == "modernization_advisor"
    assert "prompt" not in usage
    assert "cost" not in usage
