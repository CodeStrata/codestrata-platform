"""Persistence matrix checks."""

from __future__ import annotations

from pathlib import Path

from codestrata.telemetry.consent import (
    allow_session_consent,
    default_session_consent,
    deny_session_consent,
)

from verification.privacy_first_telemetry.models import CheckResult, Defect
from verification.privacy_first_telemetry.vscode_inputs import VsCodeTelemetryInventory


def check_persistence(
    monorepo: Path,
    vscode: VsCodeTelemetryInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    for label, consent in (
        ("default", default_session_consent()),
        ("allow", allow_session_consent()),
        ("deny", deny_session_consent()),
    ):
        stable = consent.to_stable_dict()
        checks.append(
            CheckResult(
                name=f"engine_consent_{label}_not_persisted_flag",
                ok=stable.get("persisted") is False
                or stable.get("persisted") is None
                or "persisted" not in stable
                or stable.get("consent_persisted") is False,
                detail=str({k: stable.get(k) for k in sorted(stable) if "persist" in k.lower()}),
                category="persistence",
                client="engine",
            )
        )

    # Engine consent module must not write files.
    import codestrata.telemetry.consent as consent_mod

    consent_src = Path(consent_mod.__file__).read_text(encoding="utf-8")
    checks.append(
        CheckResult(
            name="engine_consent_module_no_file_writes",
            ok=(
                "open(" not in consent_src
                and "Path.write" not in consent_src
                and "write_text" not in consent_src
            ),
            detail="consent.py has no filesystem writes",
            category="persistence",
            client="engine",
        )
    )

    blob = vscode.source_blob
    checks.append(
        CheckResult(
            name="vscode_no_globalState_writes",
            ok="globalState.update" not in blob and "globalState.set" not in blob,
            detail="telemetry runtime does not write globalState",
            category="persistence",
            client="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="vscode_no_workspaceState_writes",
            ok="workspaceState.update" not in blob and "workspaceState.set" not in blob,
            detail="telemetry runtime does not write workspaceState",
            category="persistence",
            client="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="vscode_no_secretStorage_writes",
            ok="secretStorage.store" not in blob,
            detail="telemetry runtime does not write secretStorage",
            category="persistence",
            client="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="vscode_consent_persisted_false",
            ok="persisted: false" in blob,
            detail="consent objects pin persisted: false",
            category="persistence",
            client="vscode",
        )
    )

    # No telemetry settings in package.json contributes.configuration
    pkg = monorepo / "vscode-plugin" / "package.json"
    pkg_text = pkg.read_text(encoding="utf-8") if pkg.is_file() else ""
    checks.append(
        CheckResult(
            name="vscode_no_telemetry_settings",
            ok='"codestrata.telemetry' not in pkg_text
            and "telemetry.enabled" not in pkg_text.lower(),
            detail="package.json has no telemetry settings",
            category="persistence",
            client="vscode",
        )
    )

    for check in checks:
        if not check.ok:
            defects.append(
                Defect(
                    classification="persistence",
                    component=check.client,
                    expected="pass",
                    actual=check.name,
                    detail=check.detail,
                )
            )
    return checks, defects
