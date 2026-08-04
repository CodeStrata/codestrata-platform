"""Extension event endpoint verification."""

from __future__ import annotations

from verification.community_cloud_api.contract import (
    INGESTION_PATHS,
    TEST_CLI_TOKEN,
    TEST_VSCODE_TOKEN,
)
from verification.community_cloud_api.credentials import auth_headers
from verification.community_cloud_api.requests import body_for


def test_extension_events_accept(verification_app) -> None:
    response = verification_app.client.post(
        INGESTION_PATHS["extension_events"],
        json=body_for("extension_events", event_id="sv7-unit-ext"),
        headers=auth_headers(TEST_VSCODE_TOKEN),
    )
    assert response.status_code == 202
    assert verification_app.sink_count("extension_events") == 1


def test_extension_events_reject_cli_principal(verification_app) -> None:
    response = verification_app.client.post(
        INGESTION_PATHS["extension_events"],
        json=body_for("extension_events", event_id="sv7-unit-ext-mismatch"),
        headers=auth_headers(TEST_CLI_TOKEN),
    )
    assert response.status_code == 403
    assert verification_app.sink_count("extension_events") == 0
