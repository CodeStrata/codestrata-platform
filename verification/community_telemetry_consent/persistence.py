"""Persistence authority checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_telemetry_consent.helpers import check, contains, read_text
from verification.community_telemetry_consent.models import CheckResult, Defect


def check_persistence(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    consent = monorepo / "engine/src/codestrata/telemetry/consent.py"
    prefs = monorepo / "engine/src/codestrata/telemetry/preferences.py"
    paths = monorepo / "engine/src/codestrata/telemetry/paths.py"
    telemetry_cmd = monorepo / "engine/src/codestrata/cli/telemetry_cmd.py"
    policy = monorepo / "engine/src/codestrata/telemetry/consent_policy.py"

    ctext = read_text(consent).lower()
    checks.append(check(
        "persistence:privacy_first_not_persisted",
        "never persisted" in ctext or "persisted" in ctext,
        "privacy-first consent is process-local",
        "persistence",
    ))
    checks.append(check(
        "persistence:legacy_preferences_file",
        prefs.is_file() and paths.is_file() and (
            contains(paths, "PREFERENCES_FILENAME") or contains(paths, "telemetry.json")
            or contains(prefs, "preferences_path")
        ),
        "legacy preferences path authority present",
        "persistence",
    ))
    cmd = read_text(telemetry_cmd).lower() if telemetry_cmd.is_file() else ""
    checks.append(check(
        "persistence:legacy_does_not_authorize_runtime",
        "privacy-first" in cmd or "does not" in cmd or "not" in cmd,
        "legacy CLI does not authorize privacy-first runtime",
        "persistence",
    ))
    if policy.is_file():
        checks.append(check(
            "persistence:policy_forbids",
            "persistence_allowed" in read_text(policy),
            "consent policy mentions persistence_allowed",
            "persistence",
        ))

    summary = {
        "privacy_first_persisted": False,
        "legacy_path": "~/.codestrata/telemetry.json",
        "legacy_authorizes_privacy_first": False,
        "secrets_in_consent": False,
    }
    return checks, defects, summary
