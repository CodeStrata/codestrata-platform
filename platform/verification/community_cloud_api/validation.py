"""Request validation and payload-limit verification."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.payload_limits import PayloadLimitPolicy

from verification.community_cloud_api.app_factory import VerificationApp, build_verification_app
from verification.community_cloud_api.contract import INGESTION_PATHS
from verification.community_cloud_api.credentials import auth_headers
from verification.community_cloud_api.models import CheckResult
from verification.community_cloud_api.requests import body_for


def check_validation(app: VerificationApp) -> list[CheckResult]:
    path = INGESTION_PATHS["telemetry"]
    headers = auth_headers()
    checks: list[CheckResult] = []

    missing = app.client.post(path, headers=headers)
    checks.append(
        CheckResult(
            name="validation:missing_body",
            ok=missing.status_code in {400, 422},
            detail=f"status={missing.status_code}",
            category="validation",
            scenario="K",
        )
    )

    wrong_media = app.client.post(
        path,
        data="not-json",
        headers={**headers, "Content-Type": "text/plain"},
    )
    checks.append(
        CheckResult(
            name="validation:wrong_media_type",
            ok=wrong_media.status_code in {400, 415},
            detail=f"status={wrong_media.status_code}",
            category="validation",
            scenario="L",
        )
    )

    malformed = app.client.post(
        path,
        data="{not-json",
        headers={**headers, "Content-Type": "application/json"},
    )
    checks.append(
        CheckResult(
            name="validation:malformed_json",
            ok=malformed.status_code == 400 and "cscc_v1_" not in malformed.text,
            detail=f"status={malformed.status_code}",
            category="validation",
            scenario="M",
        )
    )

    unknown_field = app.client.post(
        path,
        json={**body_for("telemetry", event_id="sv7-unknown-field"), "extra_field": "nope"},
        headers=headers,
    )
    checks.append(
        CheckResult(
            name="validation:unknown_fields",
            ok=unknown_field.status_code in {400, 422},
            detail=f"status={unknown_field.status_code}",
            category="validation",
            scenario="N",
        )
    )

    type_violation = app.client.post(
        path,
        json={**body_for("telemetry", event_id="sv7-type"), "event_id": 123},
        headers=headers,
    )
    checks.append(
        CheckResult(
            name="validation:strict_type",
            ok=type_violation.status_code in {400, 422},
            detail=f"status={type_violation.status_code}",
            category="validation",
            scenario="O",
        )
    )

    semantic = app.client.post(
        path,
        json=body_for("telemetry", event_id="sv7-sem", event_type="not_a_real_event"),
        headers=headers,
    )
    checks.append(
        CheckResult(
            name="validation:semantic",
            ok=semantic.status_code in {400, 422},
            detail=f"status={semantic.status_code}",
            category="validation",
            scenario="P",
        )
    )
    checks.append(
        CheckResult(
            name="validation:no_fastapi_422_leak_shape",
            ok="detail" not in unknown_field.json() or "error" in unknown_field.json(),
            detail="canonical error envelope preferred",
            category="validation",
        )
    )
    return checks


def check_payload_limits() -> list[CheckResult]:
    # Tight byte limit: schema-valid telemetry body still exceeds bytes → 413 after validation.
    policy = PayloadLimitPolicy(
        max_request_bytes=50,
        max_json_depth=8,
        max_array_length=50,
        max_object_properties=50,
        max_string_length=4_096,
        max_traversal_count=10_000,
    )
    app = build_verification_app(payload_policy=policy)
    path = INGESTION_PATHS["telemetry"]
    headers = auth_headers()

    oversized = body_for("telemetry", event_id="sv7-pay-1")
    response = app.client.post(path, json=oversized, headers=headers)
    checks = [
        CheckResult(
            name="payload:bytes_or_string_exceeded",
            ok=(
                response.status_code == 413
                and response.json()["error"]["code"] == "payload_too_large"
                and app.sink_count("telemetry") == 0
            ),
            detail=f"status={response.status_code}",
            category="payload",
            scenario="Q",
        )
    ]

    # Schema rejects deep unknown nesting before payload traversal when fields are invalid.
    deep_body = body_for("telemetry", event_id="sv7-pay-depth")
    nested = app.client.post(
        path,
        json={**deep_body, "properties": {"a": {"b": {"c": {"d": {"e": 1}}}}}},
        headers=headers,
    )
    checks.append(
        CheckResult(
            name="payload:depth_or_schema_before_sink",
            ok=nested.status_code in {400, 413, 422} and app.sink_count("telemetry") == 0,
            detail=f"status={nested.status_code}",
            category="payload",
            scenario="R",
        )
    )
    return checks
