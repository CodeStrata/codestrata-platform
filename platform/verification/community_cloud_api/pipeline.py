"""Pipeline-order failure verification."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.errors import (
    ERROR_AUTHENTICATION_REQUIRED,
    ERROR_RATE_LIMIT_EXCEEDED,
)

from verification.community_cloud_api.adapters import tight_rate_limit_policy
from verification.community_cloud_api.app_factory import build_verification_app
from verification.community_cloud_api.contract import INGESTION_PATHS
from verification.community_cloud_api.credentials import auth_headers
from verification.community_cloud_api.models import CheckResult
from verification.community_cloud_api.requests import body_for


def check_pipeline_order() -> list[CheckResult]:
    app = build_verification_app()
    checks: list[CheckResult] = []

    # Unknown route + invalid auth + malformed JSON → 404
    unknown = app.client.post(
        "/api/v1/not-a-route",
        data="{bad",
        headers={**auth_headers("not-a-token"), "Content-Type": "application/json"},
    )
    checks.append(
        CheckResult(
            name="pipeline:unknown_route_before_auth",
            ok=unknown.status_code == 404,
            detail=f"status={unknown.status_code}",
            category="pipeline",
            scenario="A",
        )
    )

    # Wrong method
    wrong = app.client.get(INGESTION_PATHS["telemetry"])
    checks.append(
        CheckResult(
            name="pipeline:wrong_method_405",
            ok=wrong.status_code == 405,
            detail=f"status={wrong.status_code}",
            category="pipeline",
            scenario="B",
        )
    )

    # Missing auth + malformed JSON → 401
    missing = app.client.post(
        INGESTION_PATHS["telemetry"],
        data="{bad",
        headers={"Content-Type": "application/json"},
    )
    checks.append(
        CheckResult(
            name="pipeline:auth_before_body",
            ok=missing.status_code == 401
            and missing.json()["error"]["code"] == ERROR_AUTHENTICATION_REQUIRED,
            detail=f"status={missing.status_code}",
            category="pipeline",
            scenario="C",
        )
    )

    # Rate limit before schema validation
    limited = build_verification_app(
        rate_limit_policy=tight_rate_limit_policy(ingestion_limit=1)
    )
    limited.client.post(
        INGESTION_PATHS["telemetry"],
        json=body_for("telemetry", event_id="sv7-pipe-rl-1"),
        headers=auth_headers(),
    )
    limited_bad = limited.client.post(
        INGESTION_PATHS["telemetry"],
        json={**body_for("telemetry", event_id="sv7-pipe-rl-2"), "extra": True},
        headers=auth_headers(),
    )
    checks.append(
        CheckResult(
            name="pipeline:rate_limit_before_validation",
            ok=limited_bad.status_code == 429
            and limited_bad.json()["error"]["code"] == ERROR_RATE_LIMIT_EXCEEDED,
            detail=f"status={limited_bad.status_code}",
            category="pipeline",
            scenario="I",
        )
    )

    # Valid auth + allowed + malformed → 400 (not 429)
    malformed = app.client.post(
        INGESTION_PATHS["telemetry"],
        data="{bad",
        headers={**auth_headers(), "Content-Type": "application/json"},
    )
    checks.append(
        CheckResult(
            name="pipeline:validation_after_auth_when_allowed",
            ok=malformed.status_code == 400,
            detail=f"status={malformed.status_code}",
            category="pipeline",
            scenario="M",
        )
    )
    return checks
