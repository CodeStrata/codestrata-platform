"""Determinism checks for cross-client verification artifacts."""

from __future__ import annotations

from codestrata.telemetry.consent import default_session_consent
from codestrata.telemetry.preview_builder import build_privacy_first_telemetry_preview

from verification.privacy_first_telemetry.models import CheckResult, Defect


def check_determinism() -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    c1 = default_session_consent().to_stable_dict()
    c2 = default_session_consent().to_stable_dict()
    checks.append(
        CheckResult(
            name="engine_consent_stable_dict_deterministic",
            ok=c1 == c2,
            detail="consent stable dict identical",
            category="determinism",
            client="engine",
        )
    )

    p1 = build_privacy_first_telemetry_preview().to_stable_json()
    p2 = build_privacy_first_telemetry_preview().to_stable_json()
    checks.append(
        CheckResult(
            name="engine_preview_json_deterministic",
            ok=p1 == p2,
            detail="preview JSON identical",
            category="determinism",
            client="engine",
        )
    )

    for check in checks:
        if not check.ok:
            defects.append(
                Defect(
                    classification="harness",
                    component=check.client,
                    expected="pass",
                    actual=check.name,
                    detail=check.detail,
                )
            )
    return checks, defects
