"""VS Code package.json surface checks (Slice 10.9 completion).

Version remains 0.2.0; no analytics commands or settings are contributed.
"""

from __future__ import annotations

import json
from pathlib import Path

from verification.anonymous_analytics_completion.models import CheckResult, Defect

_EXPECTED_VERSION = "0.2.0"


def check_vscode_surface(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    pkg_path = monorepo / "vscode-plugin" / "package.json"
    data = json.loads(pkg_path.read_text(encoding="utf-8"))

    version = data.get("version")
    checks.append(
        CheckResult(
            "vscode_surface:version_0_2_0",
            ok=version == _EXPECTED_VERSION,
            detail=str(version),
            category="vscode_surface",
        )
    )
    if version != _EXPECTED_VERSION:
        defects.append(
            Defect("CLI/VS Code surface defect", "package_version", _EXPECTED_VERSION, str(version))
        )

    commands = (data.get("contributes") or {}).get("commands") or []
    command_ids = {c.get("command", "") for c in commands}
    analytics_commands = sorted(c for c in command_ids if "analytics" in c.lower())
    checks.append(
        CheckResult(
            "vscode_surface:no_analytics_commands",
            ok=not analytics_commands,
            detail=",".join(analytics_commands),
            category="vscode_surface",
        )
    )
    if analytics_commands:
        defects.append(
            Defect(
                "CLI/VS Code surface defect",
                "analytics_commands",
                "absent",
                ",".join(analytics_commands),
            )
        )

    configuration = (
        (data.get("contributes") or {}).get("configuration") or {}
    ).get("properties") or {}
    analytics_settings = sorted(k for k in configuration if "analytics" in k.lower())
    checks.append(
        CheckResult(
            "vscode_surface:no_analytics_settings",
            ok=not analytics_settings,
            detail=",".join(analytics_settings),
            category="vscode_surface",
        )
    )
    if analytics_settings:
        defects.append(
            Defect(
                "CLI/VS Code surface defect",
                "analytics_settings",
                "absent",
                ",".join(analytics_settings),
            )
        )

    checks.append(
        CheckResult(
            "vscode_surface:assess_commands_present",
            ok="codestrata.assess" in command_ids
            and "codestrata.assessWithAi" in command_ids,
            category="vscode_surface",
        )
    )

    return checks, defects
