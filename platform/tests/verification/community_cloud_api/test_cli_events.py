"""CLI event endpoint verification."""

from __future__ import annotations

from verification.community_cloud_api.contract import INGESTION_PATHS, TEST_VSCODE_TOKEN
from verification.community_cloud_api.credentials import auth_headers
from verification.community_cloud_api.requests import body_for


def test_cli_events_accept(verification_app) -> None:
    response = verification_app.client.post(
        INGESTION_PATHS["cli_events"],
        json=body_for("cli_events", event_id="sv7-unit-cli"),
        headers=auth_headers(),
    )
    assert response.status_code == 202
    assert verification_app.sink_count("cli_events") == 1


def test_cli_events_reject_vscode_principal(verification_app) -> None:
    response = verification_app.client.post(
        INGESTION_PATHS["cli_events"],
        json=body_for("cli_events", event_id="sv7-unit-cli-mismatch"),
        headers=auth_headers(TEST_VSCODE_TOKEN),
    )
    assert response.status_code == 403
    assert verification_app.sink_count("cli_events") == 0
