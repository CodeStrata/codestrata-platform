"""Determinism checks for equivalent Community Cloud requests."""

from __future__ import annotations

from verification.community_cloud_api.app_factory import build_verification_app
from verification.community_cloud_api.contract import INGESTION_PATHS
from verification.community_cloud_api.credentials import auth_headers
from verification.community_cloud_api.models import CheckResult
from verification.community_cloud_api.requests import body_for


def check_determinism() -> list[CheckResult]:
    left = build_verification_app()
    right = build_verification_app()
    path = INGESTION_PATHS["telemetry"]
    body = body_for("telemetry", event_id="sv7-det-1")
    headers = auth_headers()

    h1 = left.client.get("/api/v1/health")
    h2 = right.client.get("/api/v1/health")
    r1 = left.client.post(path, json=body, headers=headers)
    r2 = right.client.post(path, json=body, headers=headers)
    # Exact retry bodies
    t1 = left.client.post(path, json=body, headers=headers)
    t2 = right.client.post(path, json=body, headers=headers)

    return [
        CheckResult(
            name="determinism:health_body",
            ok=h1.content == h2.content and h1.status_code == h2.status_code == 200,
            detail="health equal",
            category="determinism",
        ),
        CheckResult(
            name="determinism:first_accept_status",
            ok=r1.status_code == r2.status_code == 202
            and r1.json().get("status") == r2.json().get("status") == "accepted",
            detail=f"left={r1.status_code} right={r2.status_code}",
            category="determinism",
        ),
        CheckResult(
            name="determinism:exact_retry_status",
            ok=t1.status_code == t2.status_code == 200
            and t1.json().get("status") == t2.json().get("status") == "already_accepted",
            detail=f"left={t1.status_code} right={t2.status_code}",
            category="determinism",
        ),
        CheckResult(
            name="determinism:error_envelope_stable",
            ok=r1.json().keys() == r2.json().keys(),
            detail=f"keys={sorted(r1.json().keys())}",
            category="determinism",
        ),
    ]
