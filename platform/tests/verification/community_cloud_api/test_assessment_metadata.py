"""Assessment metadata endpoint verification."""

from __future__ import annotations

from verification.community_cloud_api.contract import INGESTION_PATHS
from verification.community_cloud_api.credentials import auth_headers
from verification.community_cloud_api.requests import body_for


def test_assessment_metadata_accept(verification_app) -> None:
    response = verification_app.client.post(
        INGESTION_PATHS["assessment_metadata"],
        json=body_for("assessment_metadata", event_id="sv7-unit-amd"),
        headers=auth_headers(),
    )
    assert response.status_code == 202
    assert verification_app.sink_count("assessment_metadata") == 1
    assert verification_app.sink_count("telemetry") == 0
    body = body_for("assessment_metadata")
    assert body["assessment"]["assessment_schema_version"] == "1.2"
