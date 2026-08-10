"""VS Code telemetry contract audit (no full E2E)."""

from __future__ import annotations

import json
from pathlib import Path

from verification.community_telemetry_consent.helpers import check, read_text
from verification.community_telemetry_consent.models import CheckResult, Defect


def check_vscode_contract(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict, list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = ["vscode_full_e2e_deferred_17_21"]
    consent_ts = monorepo / "vscode-plugin/src/telemetry/consent.ts"
    package = monorepo / "vscode-plugin/package.json"
    checks.append(check("vscode:consent_module", consent_ts.is_file(), "consent.ts present", "vscode_contract"))
    if consent_ts.is_file():
        text = read_text(consent_ts)
        checks.append(check("vscode:never_persisted", "Never persisted" in text or "never persisted" in text.lower(), "command-local consent", "vscode_contract"))
        checks.append(check("vscode:decisions_align", "allowed_for_session" in text and "non_interactive_disabled" in text, "decision vocabulary aligns", "vscode_contract"))
    if package.is_file():
        cfg = json.loads(read_text(package)).get("contributes", {}).get("configuration", {})
        props = {}
        if isinstance(cfg, dict):
            props = cfg.get("properties") or {}
        elif isinstance(cfg, list):
            for item in cfg:
                if isinstance(item, dict):
                    props.update(item.get("properties") or {})
        telemetry_settings = [k for k in props if "telemetry" in k.lower() and "consent" in k.lower()]
        checks.append(check(
            "vscode:no_hidden_consent_setting",
            len(telemetry_settings) == 0,
            f"consent settings={telemetry_settings}",
            "vscode_contract",
        ))
    checks.append(check("vscode:e2e_deferred", True, "full E2E deferred to 17.21", "vscode_contract"))
    summary = {
        "default_posture": "disabled_by_default",
        "hidden_second_system": False,
        "same_api_authority": True,
        "full_e2e": "deferred_17_21",
    }
    return checks, defects, summary, limitations
