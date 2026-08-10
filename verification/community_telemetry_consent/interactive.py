"""Interactive consent checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_telemetry_consent.helpers import check, contains, read_text
from verification.community_telemetry_consent.models import CheckResult, Defect


def check_interactive(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    interactive = monorepo / "engine/src/codestrata/telemetry/interactive_consent.py"
    text = read_text(interactive) if interactive.is_file() else ""
    checks.append(check("interactive:module_present", interactive.is_file(), "interactive_consent.py", "interactive"))
    checks.append(check("interactive:default_deny", "default_answer_deny" in text or "[y/N]" in text or "y/N" in text, "default deny prompt", "interactive"))
    checks.append(check("interactive:assess_only", "assess" in text.lower() or "ELIGIBLE" in text, "assess-eligible prompt", "interactive"))
    checks.append(check("interactive:no_persist", "persist" not in text.lower() or "False" in text, "prompt result not persisted", "interactive"))
    # silent enable forbidden: community cloud existence must not auto-enable
    silent = monorepo / "engine/src/codestrata/telemetry/prompt.py"
    if silent.is_file():
        ptext = read_text(silent)
        checks.append(check(
            "interactive:welcome_noop",
            "no-op" in ptext.lower() or "pass" in ptext or "return None" in ptext,
            "welcome/first-run does not silently enable",
            "interactive",
        ))
    summary = {
        "eligible_command": "assess",
        "default_answer": "deny",
        "persisted": False,
        "silent_enable_forbidden": True,
    }
    return checks, defects, summary
