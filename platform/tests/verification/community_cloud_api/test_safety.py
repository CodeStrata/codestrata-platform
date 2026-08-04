"""Privacy / secret-safety verification."""

from __future__ import annotations

from verification.community_cloud_api.safety import check_safety


def test_safety(verification_app) -> None:
    # Exercise one accepted request so logs/sinks exist for scanning.
    from verification.community_cloud_api.contract import INGESTION_PATHS
    from verification.community_cloud_api.credentials import auth_headers
    from verification.community_cloud_api.requests import body_for

    verification_app.client.post(
        INGESTION_PATHS["telemetry"],
        json=body_for("telemetry", event_id="sv7-safety"),
        headers=auth_headers(),
    )
    results = check_safety(verification_app)
    assert results
    assert all(item.ok for item in results), [r for r in results if not r.ok]
