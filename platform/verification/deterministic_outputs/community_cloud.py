"""Community Cloud response / event-identity determinism."""

from __future__ import annotations

from verification.deterministic_outputs.models import CheckResult


def check_community_cloud() -> list[CheckResult]:
    checks: list[CheckResult] = []
    try:
        from codestrata_platform.community_cloud_api.event_identity.fingerprint import (
            compute_payload_fingerprint,
        )
        from codestrata_platform.community_cloud_api.event_identity.identifiers import (
            build_event_key,
            build_safe_event_reference,
        )
        from codestrata_platform.community_cloud_api.event_identity.models import (
            EventIdentityScope,
        )
        from codestrata_platform.community_cloud_api.logging.context import SequenceClock
    except Exception as exc:  # noqa: BLE001
        return [
            CheckResult(
                name="community_cloud_imports",
                ok=False,
                detail=type(exc).__name__,
                category="community_cloud",
            )
        ]

    payload = {"schema_version": "1.0", "event_name": "feature_used", "n": 1}
    payload_reordered = {"n": 1, "event_name": "feature_used", "schema_version": "1.0"}
    fp1 = compute_payload_fingerprint(payload)
    fp2 = compute_payload_fingerprint(payload_reordered)
    checks.append(
        CheckResult(
            name="community_fingerprint_key_order_invariant",
            ok=fp1 == fp2 and str(fp1).startswith("fp:"),
            detail=f"fingerprint={fp1}",
            category="community_cloud",
        )
    )

    scope = EventIdentityScope(
        api_version="v1",
        client_type="cli",
        event_id="00000000-0000-4000-8000-0000000000aa",
        event_type="telemetry",
        installation_id="install-demo",
    )
    key1 = build_event_key(scope)
    key2 = build_event_key(scope)
    checks.append(
        CheckResult(
            name="community_event_key_stable",
            ok=key1 == key2 and str(key1).startswith("event:"),
            detail=f"event_key={key1}",
            category="community_cloud",
        )
    )

    ref1 = build_safe_event_reference(key1)
    ref2 = build_safe_event_reference(key1)
    checks.append(
        CheckResult(
            name="community_safe_reference_stable",
            ok=ref1 == ref2 and str(ref1).startswith("evt-"),
            detail=f"safe_ref={ref1}",
            category="community_cloud",
        )
    )

    clock = SequenceClock(start_ms=1_000_000, step_ms=0)
    t1 = clock()
    t2 = clock()
    checks.append(
        CheckResult(
            name="community_sequence_clock_stable",
            ok=t1 == t2 == 1_000_000,
            detail=f"t1={t1} t2={t2}",
            category="community_cloud",
        )
    )
    return checks
