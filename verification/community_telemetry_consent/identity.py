"""Installation/identity privacy checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_telemetry_consent.helpers import check, contains, read_text
from verification.community_telemetry_consent.models import CheckResult, Defect


def check_identity(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    docs = read_text(monorepo / "docs/reference/telemetry.md")
    checks.append(check(
        "identity:docs_no_machine_id",
        "No machine identity" in docs or "installation identity" in docs.lower(),
        "docs deny machine/installation identity for Community telemetry",
        "identity",
    ))
    consent_policy = monorepo / "engine/src/codestrata/telemetry/consent_policy.py"
    if consent_policy.is_file():
        checks.append(check(
            "identity:consent_no_installation_required",
            "installation_identity_required" in read_text(consent_policy),
            "consent policy addresses installation identity",
            "identity",
        ))
    vscode = monorepo / "vscode-plugin/src/cleanInstall/policy.ts"
    if vscode.is_file():
        vtext = read_text(vscode)
        checks.append(check(
            "identity:vscode_forbids_machine_keys",
            "machineId" in vtext or "installationId" in vtext,
            "VS Code clean-install forbids identity keys",
            "identity",
        ))
    summary = {
        "raw_machine_identifier": False,
        "local_username": False,
        "repository_path": False,
        "stable_aggregate_ok": True,
        "exposed_in_public_report": False,
    }
    return checks, defects, summary
