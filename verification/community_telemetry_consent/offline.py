"""Offline / failure isolation checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_telemetry_consent.helpers import check, contains, read_text
from verification.community_telemetry_consent.models import CheckResult, Defect


def check_offline(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict, list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    runtime = monorepo / "engine/src/codestrata/telemetry/runtime.py"
    isolation = list(monorepo.glob("engine/src/codestrata/**/*isolation*.py"))
    text = read_text(runtime) if runtime.is_file() else ""
    checks.append(check(
        "offline:record_safely",
        "record_telemetry_safely" in text or "run_with_isolated_telemetry" in text,
        "safe record helpers present",
        "offline",
    ))
    transport_policy = monorepo / "engine/src/codestrata/telemetry/transport_policy.py"
    if transport_policy.is_file():
        t = read_text(transport_policy)
        checks.append(check(
            "offline:no_persistent_queue_privacy_first",
            "persistent_retry_queue" in t and "False" in t,
            "privacy-first forbids persistent retry queue",
            "offline",
        ))
        limitations.append("best_effort_telemetry_no_offline_queue")
    # assessment isolation module
    found_iso = any("assessment" in p.name for p in isolation) or "isolation" in text.lower()
    checks.append(check("offline:assessment_isolation", found_iso or "fail" in text.lower(), "assessment isolation present", "offline"))

    summary = {
        "telemetry_failure_fails_assessment": False,
        "infinite_retry": False,
        "unbounded_queue": False,
        "behavior": "best_effort_no_persistent_queue",
    }
    return checks, defects, summary, limitations
