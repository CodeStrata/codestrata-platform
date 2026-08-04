"""Structured logging verification."""

from __future__ import annotations

from verification.community_cloud_api.app_factory import VerificationApp
from verification.community_cloud_api.contract import INGESTION_PATHS, TEST_CLI_TOKEN
from verification.community_cloud_api.credentials import auth_headers
from verification.community_cloud_api.models import CheckResult
from verification.community_cloud_api.requests import body_for


def check_logging(app: VerificationApp) -> list[CheckResult]:
    before = len(app.log_sink.lines)
    app.client.get("/api/v1/health")
    app.client.post(
        INGESTION_PATHS["telemetry"],
        json=body_for("telemetry", event_id="sv7-log-1"),
        headers=auth_headers(),
    )
    lines = app.log_sink.lines[before:]
    blob = "".join(lines)
    events = []
    try:
        events = app.log_sink.events()
    except Exception:  # noqa: BLE001
        events = []
    event_types = {str(item.get("event_type") or item.get("type") or "") for item in events}
    flattened = " ".join(event_types).lower() + blob.lower()
    checks = [
        CheckResult(
            name="logging:emits_on_health_and_ingest",
            ok=len(lines) > 0,
            detail=f"lines={len(lines)}",
            category="logging",
        ),
        CheckResult(
            name="logging:no_credentials",
            ok=TEST_CLI_TOKEN not in blob and "Authorization" not in blob,
            detail="no credential/header leakage",
            category="logging",
        ),
        CheckResult(
            name="logging:no_raw_event_id",
            ok="sv7-log-1" not in blob,
            detail="raw event id absent",
            category="logging",
        ),
        CheckResult(
            name="logging:lifecycle_signal",
            ok=(
                "request" in flattened
                or "health" in flattened
                or "telemetry" in flattened
                or "authentication" in flattened
            ),
            detail=f"types={sorted(event_types)[:8]}",
            category="logging",
        ),
    ]
    return checks
