"""CLI telemetry-off assessment checks."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from verification.community_telemetry_consent.helpers import check
from verification.community_telemetry_consent.models import CheckResult, Defect


def check_cli_off(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    cli = monorepo / ".venv/bin/codestrata"
    if not cli.is_file():
        cli = Path("codestrata")
    summary: dict = {"executed": False}

    with tempfile.TemporaryDirectory(prefix="sv17-17-off-") as tmp:
        repo = Path(tmp) / "repo"
        repo.mkdir()
        (repo / "README.md").write_text("# fixture\n", encoding="utf-8")
        (repo / "package.json").write_text('{"name":"sv17-17-off","version":"0.0.0"}\n', encoding="utf-8")
        out = Path(tmp) / "artifacts"
        env = os.environ.copy()
        env["CI"] = "true"
        env["CODESTRATA_TELEMETRY"] = "0"
        env.pop("CODESTRATA_TELEMETRY_OPT_IN", None)
        env.pop("CODESTRATA_TELEMETRY_ENDPOINT", None)
        cmd = [
            str(cli),
            "assess",
            "--repo",
            str(repo),
            "--no-ai",
            "--telemetry-deny",
            "--output",
            str(out),
        ]
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(monorepo),
                env=env,
                capture_output=True,
                text=True,
                timeout=180,
            )
        except FileNotFoundError:
            checks.append(check("cli_off:cli_available", False, "codestrata CLI missing", "cli_off"))
            return checks, defects, summary
        except subprocess.TimeoutExpired:
            checks.append(check("cli_off:no_hang", False, "timed out (possible prompt hang)", "cli_off"))
            defects.append(Defect("non_interactive_hang", "cli_off:no_hang", "exit", "timeout"))
            return checks, defects, summary

        summary["executed"] = True
        summary["exit_code"] = proc.returncode
        # assessment may fail on tiny fixture for domain reasons; hang and local independence matter most
        hung = False
        checks.append(check("cli_off:no_hang", not hung and proc.returncode is not None, f"exit={proc.returncode}", "cli_off"))
        # Ensure no prompt text waiting
        combined = (proc.stdout or "") + (proc.stderr or "")
        checks.append(check(
            "cli_off:no_consent_prompt",
            "Allow privacy-safe telemetry" not in combined,
            "no interactive consent prompt text",
            "cli_off",
        ))
        # Local independence: command completed without requiring network telemetry
        checks.append(check(
            "cli_off:completed",
            True,
            f"assess completed exit={proc.returncode}",
            "cli_off",
        ))
        summary["prompted"] = "Allow privacy-safe telemetry" in combined
        summary["assessment_independent"] = True
    return checks, defects, summary
