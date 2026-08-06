"""Consent boundary checks (Slice 10.9 completion).

Reuses Slice 10.8's ``check_consent`` and adds an explicit check that Engine
analytics does not use legacy telemetry consent/preferences as an
authorization gate, and that VS Code analytics remains command-local.
"""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_completion.inventory import (
    EngineAnalyticsInventory,
    VsCodeAnalyticsInventory,
    adapt_checks,
)
from verification.anonymous_analytics_completion.models import CheckResult, Defect
from verification.anonymous_analytics_privacy.consent import (
    check_consent as _check_consent_108,
)

_LEGACY_CONSENT_NEEDLES: tuple[str, ...] = (
    "from codestrata.telemetry.consent",
    "from codestrata.telemetry.consent_policy",
    "from codestrata.telemetry.cli_consent",
    "SessionConsent",
    "InteractiveConsent",
)


def check_consent(
    monorepo: Path,
    engine: EngineAnalyticsInventory,
    vscode: VsCodeAnalyticsInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    raw_checks, raw_defects = _check_consent_108(engine, vscode, monorepo)
    checks, defects = adapt_checks(raw_checks, raw_defects)

    analytics_root = monorepo / "engine" / "src" / "codestrata" / "telemetry" / "analytics"
    hits: list[str] = []
    for path in sorted(analytics_root.glob("*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for needle in _LEGACY_CONSENT_NEEDLES:
            if needle in text:
                hits.append(f"{path.name}:{needle}")
    checks.append(
        CheckResult(
            "consent:engine_no_legacy_prefs_as_auth",
            ok=not hits,
            detail=",".join(hits[:5]) if hits else "clean",
            category="consent",
        )
    )
    if hits:
        defects.append(
            Defect(
                "consent defect",
                "legacy_prefs_as_auth",
                "not used as analytics authorization",
                ",".join(hits[:5]),
            )
        )

    checks.append(
        CheckResult(
            "consent:vscode_command_local_not_global_setting",
            ok="allowed_for_session" in vscode.source_blob
            and "codestrata.analytics.enabled" not in vscode.package_json_text,
            category="consent",
        )
    )

    return checks, defects
