"""Engine CLI analytics surface checks (Slice 10.9 completion).

No analytics status/preview/send/flush/identity commands exist. Epic 9
telemetry commands remain untouched.
"""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_completion.models import CheckResult, Defect

_FORBIDDEN_ANALYTICS_TOKENS: tuple[str, ...] = (
    "analytics-status",
    "analytics_status",
    "analytics-preview",
    "analytics_preview",
    "analytics-send",
    "analytics_send",
    "analytics-flush",
    "analytics_flush",
    "analytics-identity",
    "analytics_identity",
    '"analytics"',
    "analytics_app",
)

_REQUIRED_EPIC9_TELEMETRY_COMMANDS: tuple[str, ...] = (
    "status",
    "preview",
    "enable",
    "disable",
    "reset",
    "show",
)


def check_cli_surface(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    cli_root = monorepo / "engine" / "src" / "codestrata" / "cli"
    telemetry_cmd = (cli_root / "telemetry_cmd.py").read_text(encoding="utf-8")
    assess = (cli_root / "assess.py").read_text(encoding="utf-8")
    combined = telemetry_cmd + "\n" + assess

    checks.append(
        CheckResult(
            "cli:no_dedicated_analytics_command_module",
            ok=not (cli_root / "analytics_cmd.py").exists(),
            category="cli",
        )
    )

    for token in _FORBIDDEN_ANALYTICS_TOKENS:
        ok = token not in combined
        checks.append(
            CheckResult(
                f"cli:forbidden_token:{token.strip('_-\"').replace('-', '_')}",
                ok=ok,
                detail=token,
                category="cli",
            )
        )
        if not ok:
            defects.append(
                Defect("CLI/VS Code surface defect", token, "absent", "present")
            )

    for cmd in _REQUIRED_EPIC9_TELEMETRY_COMMANDS:
        ok = f'command("{cmd}")' in telemetry_cmd
        checks.append(
            CheckResult(
                f"cli:epic9_telemetry_command_preserved:{cmd}",
                ok=ok,
                category="cli",
            )
        )
        if not ok:
            defects.append(
                Defect("CLI/VS Code surface defect", cmd, "present", "missing")
            )

    checks.append(
        CheckResult(
            "cli:assess_no_analytics_flags",
            ok="--analytics" not in assess and "--send-analytics" not in assess,
            category="cli",
        )
    )
    if "--analytics" in assess or "--send-analytics" in assess:
        defects.append(
            Defect("CLI/VS Code surface defect", "assess_analytics_flag", "absent", "present")
        )

    return checks, defects
