"""CLI and VS Code contribution surface verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.privacy_first_telemetry_completion.models import CheckResult, Defect

_FORBIDDEN_ASSESS_FLAGS = (
    "--telemetry-endpoint",
    "--telemetry-url",
    "--telemetry-token",
    "--telemetry-queue",
    "--installation-id",
)

_FORBIDDEN_TELEMETRY_COMMANDS = (
    "flush",
    "send-test",
    "send_test",
    "queue",
    "install-id",
    "debug-payload",
)


def check_cli_surface(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    assess = (monorepo / "engine" / "src" / "codestrata" / "cli" / "assess.py").read_text(
        encoding="utf-8"
    )
    telemetry_cmd = (
        monorepo / "engine" / "src" / "codestrata" / "cli" / "telemetry_cmd.py"
    ).read_text(encoding="utf-8")

    checks.append(
        CheckResult(
            name="cli_assess_telemetry_allow",
            ok="--telemetry-allow" in assess,
            detail="assess --telemetry-allow",
            category="cli",
        )
    )
    checks.append(
        CheckResult(
            name="cli_assess_telemetry_deny",
            ok="--telemetry-deny" in assess,
            detail="assess --telemetry-deny",
            category="cli",
        )
    )
    checks.append(
        CheckResult(
            name="cli_telemetry_status",
            ok='command("status")' in telemetry_cmd or 'name="status"' in telemetry_cmd,
            detail="telemetry status",
            category="cli",
        )
    )
    checks.append(
        CheckResult(
            name="cli_telemetry_preview",
            ok='command("preview")' in telemetry_cmd or 'name="preview"' in telemetry_cmd,
            detail="telemetry preview",
            category="cli",
        )
    )
    for legacy in ("enable", "disable", "reset", "show"):
        checks.append(
            CheckResult(
                name=f"cli_legacy_{legacy}",
                ok=f'command("{legacy}")' in telemetry_cmd,
                detail=f"legacy telemetry {legacy}",
                category="cli",
            )
        )

    for flag in _FORBIDDEN_ASSESS_FLAGS:
        checks.append(
            CheckResult(
                name=f"cli_forbidden_flag_{flag.strip('-').replace('-', '_')}",
                ok=flag not in assess and flag not in telemetry_cmd,
                detail=flag,
                category="cli",
            )
        )
    for cmd in _FORBIDDEN_TELEMETRY_COMMANDS:
        checks.append(
            CheckResult(
                name=f"cli_forbidden_command_{cmd.replace('-', '_')}",
                ok=f'command("{cmd}")' not in telemetry_cmd,
                detail=cmd,
                category="cli",
            )
        )

    # Unrelated commands should not gain telemetry flags (scan.py if present).
    scan = monorepo / "engine" / "src" / "codestrata" / "cli" / "scan.py"
    if scan.is_file():
        scan_text = scan.read_text(encoding="utf-8")
        checks.append(
            CheckResult(
                name="cli_scan_no_telemetry_flags",
                ok="--telemetry-allow" not in scan_text,
                detail="scan without telemetry flags",
                category="cli",
            )
        )

    for check in checks:
        if not check.ok:
            defects.append(
                Defect(
                    classification="CLI/VS Code surface defect",
                    component="cli",
                    expected="pass",
                    actual=check.name,
                    detail=check.detail,
                )
            )
    return checks, defects


def check_vscode_surface(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    pkg_path = monorepo / "vscode-plugin" / "package.json"
    data = json.loads(pkg_path.read_text(encoding="utf-8"))
    configuration = (
        ((data.get("contributes") or {}).get("configuration") or {}).get("properties")
        or {}
    )
    commands = ((data.get("contributes") or {}).get("commands") or [])
    command_ids = {c.get("command", "") for c in commands}

    forbidden_settings = (
        "codestrata.telemetry.enabled",
        "codestrata.telemetry.endpoint",
        "codestrata.telemetry.token",
        "telemetry.enabled",
    )
    for setting in forbidden_settings:
        checks.append(
            CheckResult(
                name=f"vscode_no_setting_{setting.replace('.', '_')}",
                ok=setting not in configuration,
                detail=setting,
                category="vscode_surface",
            )
        )

    telemetry_commands = [c for c in command_ids if "telemetry" in c.lower()]
    checks.append(
        CheckResult(
            name="vscode_no_telemetry_commands",
            ok=not telemetry_commands,
            detail=str(telemetry_commands) if telemetry_commands else "none",
            category="vscode_surface",
        )
    )
    checks.append(
        CheckResult(
            name="vscode_assess_commands_present",
            ok="codestrata.assess" in command_ids
            and "codestrata.assessWithAi" in command_ids,
            detail="assess + assessWithAi",
            category="vscode_surface",
        )
    )

    pkg_text = pkg_path.read_text(encoding="utf-8")
    checks.append(
        CheckResult(
            name="vscode_no_telemetry_statusbar",
            ok='"telemetryStatus"' not in pkg_text
            and "createStatusBarItem" not in pkg_text,
            detail="no telemetry status bar contribution",
            category="vscode_surface",
        )
    )

    for check in checks:
        if not check.ok:
            defects.append(
                Defect(
                    classification="CLI/VS Code surface defect",
                    component="vscode",
                    expected="pass",
                    actual=check.name,
                    detail=check.detail,
                )
            )
    return checks, defects
