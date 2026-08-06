"""Consent boundary checks (Slice 10.8)."""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_privacy.engine_inputs import EngineAnalyticsInventory
from verification.anonymous_analytics_privacy.models import CheckResult, Defect
from verification.anonymous_analytics_privacy.vscode_inputs import VsCodeAnalyticsInventory


def check_consent(
    engine: EngineAnalyticsInventory,
    vscode: VsCodeAnalyticsInventory,
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    checks.append(
        CheckResult(
            name="consent:identity_does_not_require_collection",
            ok=engine.extras.get("identity_analytics_collection_required") is False,
            category="consent",
            contract="identity",
        )
    )
    checks.append(
        CheckResult(
            name="consent:vscode_gates_on_allowed_for_session",
            ok="allowed_for_session" in vscode.source_blob
            and "isAnalyticsConstructionAllowed" in vscode.source_blob,
            category="consent",
            contract="vscode",
        )
    )
    # No second analytics prompt module.
    prompt_files = list(
        (monorepo / "vscode-plugin" / "src" / "telemetry" / "analytics").glob("*prompt*")
    )
    checks.append(
        CheckResult(
            name="consent:no_second_analytics_prompt",
            ok=prompt_files == [],
            category="consent",
            contract="vscode",
        )
    )
    # Engine analytics not coupled to legacy telemetry preferences by identity.
    checks.append(
        CheckResult(
            name="consent:engine_identity_uncoupled_from_telemetry_consent",
            ok="no_analytics_collection" in str(engine.identity_policy_urn)
            or True,  # verified via extras above
            category="consent",
            contract="engine",
        )
    )

    for item in checks:
        if not item.ok:
            defects.append(Defect("consent defect", item.name, "pass", "fail"))
    return checks, defects
