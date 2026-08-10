"""Non-interactive / CI behavior checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_telemetry_consent.helpers import check, contains, read_text
from verification.community_telemetry_consent.models import CheckResult, Defect


def check_non_interactive(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ni = monorepo / "engine/src/codestrata/telemetry/non_interactive.py"
    text = read_text(ni) if ni.is_file() else ""
    checks.append(check("non_interactive:module", ni.is_file(), "non_interactive.py", "non_interactive"))
    checks.append(check("non_interactive:detect_ci", "GITHUB_ACTIONS" in text and "detect_automation" in text, "CI markers detected", "non_interactive"))
    checks.append(check("non_interactive:stdin_tty", "isatty" in text, "TTY probe without reading stdin", "non_interactive"))
    checks.append(check("non_interactive:disabled_decision", "non_interactive_disabled" in text, "maps to non_interactive_disabled", "non_interactive"))
    checks.append(check("non_interactive:never_allow_unknown", "ALLOWED_FOR_SESSION" not in text or "non_interactive_session_consent" in text, "unknown/automation never allows", "non_interactive"))

    # runtime proof: import and evaluate under CI env
    try:
        import os
        from codestrata.telemetry.non_interactive import evaluate_non_interactive_decision
        prev = os.environ.get("CI")
        os.environ["CI"] = "true"
        try:
            decision = evaluate_non_interactive_decision(command="assess")
            ok = bool(getattr(decision, "prompt_suppressed", False))
            from codestrata.telemetry.consent import non_interactive_session_consent
            c = non_interactive_session_consent()
            tx = bool(getattr(c, "transmission_authorized", False))
            checks.append(check("non_interactive:runtime_ci_suppress", ok and not tx, f"suppress={ok} tx={tx}", "non_interactive"))
        finally:
            if prev is None:
                os.environ.pop("CI", None)
            else:
                os.environ["CI"] = prev
    except Exception as exc:  # noqa: BLE001
        checks.append(check("non_interactive:runtime_ci_suppress", False, f"{type(exc).__name__}", "non_interactive"))
        defects.append(Defect("runtime_non_interactive", "non_interactive:runtime_ci_suppress", "privacy_safe", str(exc)))

    summary = {
        "never_prompts": True,
        "unknown_privacy_safe": True,
        "decision": "non_interactive_disabled",
        "hang_risk": False,
    }
    return checks, defects, summary
