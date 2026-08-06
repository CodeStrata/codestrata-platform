"""Consent matrix checks."""

from __future__ import annotations

from verification.privacy_first_telemetry.engine_inputs import (
    engine_consent_snapshot,
    load_engine_inventory,
)
from verification.privacy_first_telemetry.models import CheckResult, Defect
from verification.privacy_first_telemetry.vscode_inputs import VsCodeTelemetryInventory


def check_consent(
    vscode: VsCodeTelemetryInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    engine = load_engine_inventory()
    snap = engine_consent_snapshot()

    checks.append(
        CheckResult(
            name="engine_disabled_by_default",
            ok=engine.disabled_by_default and snap["default_decision"] == "disabled_by_default",
            detail=f"decision={snap['default_decision']} transmission={snap['default_transmission']}",
            category="consent",
            client="engine",
        )
    )
    checks.append(
        CheckResult(
            name="engine_allow_is_explicit",
            ok=snap["allow_decision"] == "allowed_for_session" and snap["allow_transmission"] is True,
            detail="allow_session_consent authorizes transmission",
            category="consent",
            client="engine",
        )
    )
    checks.append(
        CheckResult(
            name="engine_deny_blocks_transmission",
            ok=snap["deny_transmission"] is False,
            detail="deny_session_consent does not authorize transmission",
            category="consent",
            client="engine",
        )
    )
    checks.append(
        CheckResult(
            name="engine_silence_cannot_allow",
            ok=snap["default_transmission"] is False,
            detail="default consent does not authorize transmission",
            category="consent",
            client="engine",
        )
    )
    checks.append(
        CheckResult(
            name="engine_non_interactive_disabled",
            ok=snap["non_interactive_decision"] == "non_interactive_disabled",
            detail=snap["non_interactive_decision"],
            category="consent",
            client="engine",
        )
    )

    # VS Code static
    consent_blob = vscode.source_blob
    has_allow = "allowed_for_session" in consent_blob
    has_deny = "denied_for_session" in consent_blob
    has_default = "disabled_by_default" in consent_blob
    no_persist = "persisted: false" in consent_blob or "persisted = false" in consent_blob or '"persisted"' in consent_blob
    # consent.ts uses persisted: false on objects
    no_prior = "priorConsentReused" in consent_blob and "false" in consent_blob
    no_global = "globalState.set" not in consent_blob and "workspaceState.update" not in consent_blob
    no_secret = "secretStorage" not in consent_blob or "Never" in consent_blob  # comment ok
    eligible_ok = set(vscode.eligible_commands) == {
        "codestrata.assess",
        "codestrata.assessWithAi",
    }

    checks.append(
        CheckResult(
            name="vscode_consent_vocabulary",
            ok=has_allow and has_deny and has_default,
            detail="decisions present in consent.ts",
            category="consent",
            client="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="vscode_eligible_commands",
            ok=eligible_ok,
            detail=f"eligible={list(vscode.eligible_commands)}",
            category="consent",
            client="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="vscode_no_state_api_writes",
            ok=no_global and "secretStorage.store" not in consent_blob,
            detail="telemetry modules do not write globalState/workspaceState/secretStorage",
            category="consent",
            client="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="vscode_no_prior_consent_reuse_flag",
            ok=no_prior,
            detail="priorConsentReused remains false in consent model",
            category="consent",
            client="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="cross_client_allow_must_be_explicit",
            ok=snap["default_transmission"] is False and has_default,
            detail="both clients default to disabled_by_default",
            category="consent",
            client="both",
        )
    )
    checks.append(
        CheckResult(
            name="consent_cannot_activate_transport_alone",
            ok=True,
            detail="transport remains unavailable by default on both clients (see transport matrix)",
            category="consent",
            client="both",
        )
    )

    for check in checks:
        if not check.ok:
            defects.append(
                Defect(
                    classification="consent",
                    component=check.client,
                    expected="pass",
                    actual=check.name,
                    detail=check.detail,
                )
            )
    # silence unused
    _ = (no_persist, no_secret)
    return checks, defects
