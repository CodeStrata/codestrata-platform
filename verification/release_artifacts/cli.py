"""CLI help surface checks for release artifact verification."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from verification.release_artifacts.models import CheckResult, Defect


_REQUIRED_MARKERS = ("assess", "init", "doctor", "version")
_FORBIDDEN_MARKERS = ("tofu", " eir ", "infrastructure")


def _codestrata_help(monorepo: Path) -> tuple[int, str]:
    """Prefer the monorepo venv console script (Typer entry point)."""

    codestrata = monorepo / ".venv" / "bin" / "codestrata"
    if codestrata.is_file():
        command = [str(codestrata), "--help"]
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
    else:
        python = monorepo / ".venv" / "bin" / "python"
        command = [
            str(python),
            "-c",
            "from codestrata.cli import app; app(prog_name='codestrata')",
            "--help",
        ]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(monorepo / "engine" / "src")
    completed = subprocess.run(
        command,
        cwd=str(monorepo),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    return completed.returncode, (completed.stdout or "") + (completed.stderr or "")


def check_cli_surface(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    exit_code, text = _codestrata_help(monorepo)
    lowered = text.lower()

    checks.append(
        CheckResult(
            name="cli:help_exit",
            ok=exit_code == 0,
            detail=f"exit={exit_code}",
            category="cli",
        )
    )

    for marker in _REQUIRED_MARKERS:
        ok = marker in lowered
        checks.append(
            CheckResult(
                name=f"cli:help_has_{marker}",
                ok=ok,
                detail=f"present={ok}",
                category="cli",
            )
        )
        if not ok:
            defects.append(
                Defect(
                    classification="cli_surface",
                    component="codestrata --help",
                    expected=marker,
                    actual="missing",
                )
            )

    for marker in _FORBIDDEN_MARKERS:
        token = marker.strip()
        forbidden = f"\n  {token}\n" in lowered or f"│ {token} " in lowered
        checks.append(
            CheckResult(
                name=f"cli:help_no_{token}",
                ok=not forbidden,
                detail=f"forbidden_present={forbidden}",
                category="cli",
            )
        )
        if forbidden:
            defects.append(
                Defect(
                    classification="cli_surface",
                    component="codestrata --help",
                    expected=f"no {token} command group",
                    actual="present",
                )
            )

    return checks, defects
