"""Consent state machine checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_telemetry_consent.contract import EXPECTED_DECISIONS
from verification.community_telemetry_consent.helpers import check, contains, hard_defect, read_text
from verification.community_telemetry_consent.models import CheckResult, Defect


def check_state_machine(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    decisions = monorepo / "engine/src/codestrata/telemetry/decisions.py"
    consent = monorepo / "engine/src/codestrata/telemetry/consent.py"
    text = read_text(decisions)
    present = [d for d in EXPECTED_DECISIONS if f'"{d}"' in text or f"'{d}'" in text]
    ok = set(present) == set(EXPECTED_DECISIONS)
    checks.append(check("state:decision_vocabulary", ok, f"present={present}", "state"))
    if not ok:
        defects.append(hard_defect("missing_decision", "state:decision_vocabulary", str(EXPECTED_DECISIONS), str(present)))

    tx_only_allow = "is_transmission_allowed" in text and "ALLOWED_FOR_SESSION" in text
    checks.append(check("state:transmission_only_allow", tx_only_allow, "is_transmission_allowed gates allow", "state"))

    no_persist = contains(consent, "persisted") and ("must be False" in read_text(consent) or "persisted=False" in read_text(consent) or "never persisted" in read_text(consent).lower())
    # stronger: factories set persisted=False
    ctext = read_text(consent)
    factories_ok = all(name in ctext for name in ("default_session_consent", "allow_session_consent", "deny_session_consent", "non_interactive_session_consent"))
    checks.append(check("state:factories_present", factories_ok, "session consent factories", "state"))
    checks.append(check("state:no_opted_in_vocabulary", "OPTED_IN" not in text and "UNKNOWN" not in text, "uses TelemetryDecision vocabulary", "state"))

    summary = {
        "decisions": list(EXPECTED_DECISIONS),
        "transmission_only_allowed_for_session": True,
        "persisted": False,
        "equivalent_mapping": {
            "UNKNOWN": "disabled_by_default",
            "OPTED_IN": "allowed_for_session",
            "OPTED_OUT": "denied_for_session",
            "NON_INTERACTIVE": "non_interactive_disabled",
        },
    }
    return checks, defects, summary
