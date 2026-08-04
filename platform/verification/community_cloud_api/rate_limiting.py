"""Rate-limit verification."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.errors import ERROR_RATE_LIMIT_EXCEEDED

from verification.community_cloud_api.adapters import tight_rate_limit_policy
from verification.community_cloud_api.app_factory import build_verification_app
from verification.community_cloud_api.contract import INGESTION_PATHS
from verification.community_cloud_api.credentials import auth_headers
from verification.community_cloud_api.models import CheckResult
from verification.community_cloud_api.requests import body_for


def check_rate_limiting() -> list[CheckResult]:
    app = build_verification_app(
        rate_limit_policy=tight_rate_limit_policy(ingestion_limit=1)
    )
    path = INGESTION_PATHS["telemetry"]
    first = app.client.post(
        path,
        json=body_for("telemetry", event_id="sv7-rl-1"),
        headers=auth_headers(),
    )
    second = app.client.post(
        path,
        json=body_for("telemetry", event_id="sv7-rl-2"),
        headers={**auth_headers(), "X-Forwarded-For": "1.2.3.4", "X-Real-IP": "5.6.7.8"},
    )
    checks = [
        CheckResult(
            name="rate_limit:first_allowed",
            ok=first.status_code == 202,
            detail=f"status={first.status_code}",
            category="rate_limit",
        ),
        CheckResult(
            name="rate_limit:second_exceeded",
            ok=second.status_code == 429
            and second.json()["error"]["code"] == ERROR_RATE_LIMIT_EXCEEDED,
            detail=f"status={second.status_code}",
            category="rate_limit",
            scenario="I",
        ),
        CheckResult(
            name="rate_limit:forwarded_headers_ignored",
            ok=second.status_code == 429,
            detail="X-Forwarded-For did not bypass",
            category="rate_limit",
        ),
        CheckResult(
            name="rate_limit:no_sink_on_exceeded",
            ok=app.sink_count("telemetry") == 1,
            detail=f"sinks={app.sink_count('telemetry')}",
            category="rate_limit",
        ),
        CheckResult(
            name="rate_limit:no_raw_ip_in_response",
            ok="1.2.3.4" not in second.text and "5.6.7.8" not in second.text,
            detail="no IP echo",
            category="rate_limit",
        ),
    ]

    unavailable = build_verification_app(unavailable_rate_limit_store=True)
    blocked = unavailable.client.post(
        path,
        json=body_for("telemetry", event_id="sv7-rl-store-down"),
        headers=auth_headers(),
    )
    checks.append(
        CheckResult(
            name="rate_limit:store_unavailable",
            ok=blocked.status_code == 503,
            detail=f"status={blocked.status_code}",
            category="rate_limit",
            scenario="J",
        )
    )
    return checks
