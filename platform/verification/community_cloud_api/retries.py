"""Event-identity and retry verification for all ingestion endpoints."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.errors import ERROR_EVENT_IDENTITY_CONFLICT

from verification.community_cloud_api.app_factory import VerificationApp, build_verification_app
from verification.community_cloud_api.contract import INGESTION_KINDS, INGESTION_PATHS
from verification.community_cloud_api.credentials import auth_headers, token_for_kind
from verification.community_cloud_api.models import CheckResult
from verification.community_cloud_api.requests import body_for, conflict_body_for


def check_retries(app: VerificationApp) -> list[CheckResult]:
    checks: list[CheckResult] = []
    for kind in INGESTION_KINDS:
        path = INGESTION_PATHS[kind]
        headers = auth_headers(token_for_kind(kind))
        event_id = f"sv7-retry-{kind}"
        first = app.client.post(path, json=body_for(kind, event_id=event_id), headers=headers)
        sinks_after_first = app.sink_count(kind)
        identity_after_first = app.identity_count()
        exact = app.client.post(path, json=body_for(kind, event_id=event_id), headers=headers)
        conflict = app.client.post(
            path,
            json={**conflict_body_for(kind), "event_id": event_id},
            headers=headers,
        )
        checks.append(
            CheckResult(
                name=f"retry:first_accepted:{kind}",
                ok=first.status_code == 202 and first.json().get("status") == "accepted",
                detail=f"status={first.status_code}",
                category="retry",
            )
        )
        checks.append(
            CheckResult(
                name=f"retry:exact:{kind}",
                ok=(
                    exact.status_code == 200
                    and exact.json().get("status") == "already_accepted"
                    and app.sink_count(kind) == sinks_after_first
                    and app.identity_count() == identity_after_first
                ),
                detail=f"status={exact.status_code} sinks={app.sink_count(kind)}",
                category="retry",
            )
        )
        checks.append(
            CheckResult(
                name=f"retry:conflict:{kind}",
                ok=(
                    conflict.status_code == 409
                    and conflict.json()["error"]["code"] == ERROR_EVENT_IDENTITY_CONFLICT
                    and app.sink_count(kind) == sinks_after_first
                    and event_id not in conflict.text
                ),
                detail=f"status={conflict.status_code}",
                category="retry",
                scenario="U",
            )
        )

    unavailable = build_verification_app(unavailable_identity=True)
    blocked = unavailable.client.post(
        INGESTION_PATHS["telemetry"],
        json=body_for("telemetry", event_id="sv7-id-unavailable"),
        headers=auth_headers(),
    )
    checks.append(
        CheckResult(
            name="retry:identity_unavailable",
            ok=blocked.status_code == 503 and unavailable.sink_count("telemetry") == 0,
            detail=f"status={blocked.status_code}",
            category="retry",
            scenario="T",
        )
    )

    sink_down = build_verification_app(unavailable_sinks=True)
    sink_resp = sink_down.client.post(
        INGESTION_PATHS["telemetry"],
        json=body_for("telemetry", event_id="sv7-sink-down"),
        headers=auth_headers(),
    )
    checks.append(
        CheckResult(
            name="retry:sink_unavailable",
            ok=sink_resp.status_code == 503 and sink_down.identity_count() == 0,
            detail=f"status={sink_resp.status_code}",
            category="retry",
            scenario="V",
        )
    )
    return checks


def check_endpoint_separation(app: VerificationApp) -> list[CheckResult]:
    """CLI payload rejected by extension route; sinks stay isolated."""

    checks: list[CheckResult] = []
    # CLI body on extension endpoint with VS Code auth → schema/client mismatch
    response = app.client.post(
        INGESTION_PATHS["extension_events"],
        json=body_for("cli_events", event_id="sv7-sep-cli-on-ext"),
        headers=auth_headers(token_for_kind("extension_events")),
    )
    checks.append(
        CheckResult(
            name="separation:cli_body_on_extension",
            ok=response.status_code in {400, 403, 422},
            detail=f"status={response.status_code}",
            category="separation",
        )
    )

    before = {k: app.sink_count(k) for k in INGESTION_KINDS}
    app.client.post(
        INGESTION_PATHS["telemetry"],
        json=body_for("telemetry", event_id="sv7-sep-tel-only"),
        headers=auth_headers(),
    )
    after = {k: app.sink_count(k) for k in INGESTION_KINDS}
    others_unchanged = all(
        after[k] == before[k] for k in INGESTION_KINDS if k != "telemetry"
    )
    checks.append(
        CheckResult(
            name="separation:telemetry_sink_isolated",
            ok=after["telemetry"] == before["telemetry"] + 1 and others_unchanged,
            detail=f"delta_telemetry={after['telemetry'] - before['telemetry']}",
            category="separation",
        )
    )
    return checks
