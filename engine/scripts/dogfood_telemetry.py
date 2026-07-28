#!/usr/bin/env python3
"""Dogfood validation for Phase 14.3 telemetry (local only; no network required)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    engine_root = Path(__file__).resolve().parents[1]
    src = engine_root / "src"
    codestrata_bin = shutil.which("codestrata")
    with tempfile.TemporaryDirectory(prefix="cs-telemetry-dogfood-") as tmp:
        home = Path(tmp)
        env = os.environ.copy()
        env["CODESTRATA_HOME"] = str(home)
        env["PYTHONPATH"] = str(src) + (
            os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
        )
        env["CODESTRATA_TELEMETRY_SKIP_PROMPT"] = "1"
        env["CODESTRATA_CLI_MACHINE"] = "1"
        env.pop("CODESTRATA_TELEMETRY", None)
        env.pop("CODESTRATA_TELEMETRY_ENDPOINT", None)
        py = sys.executable

        def run(*args: str) -> subprocess.CompletedProcess[str]:
            if codestrata_bin:
                cmd = [codestrata_bin, *args]
            else:
                # Fallback: invoke Typer app with rewritten argv.
                cmd = [
                    py,
                    "-c",
                    (
                        "import sys; from codestrata.cli import app; "
                        "sys.argv = ['codestrata'] + sys.argv[1:]; app(standalone_mode=True)"
                    ),
                    *args,
                ]
            return subprocess.run(
                cmd,
                cwd=engine_root,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )

        steps: list[tuple[str, bool, str]] = []

        status = run("telemetry", "status")
        try:
            payload = json.loads(status.stdout)
            steps.append(("status command", status.returncode == 0, status.stderr))
            steps.append(
                ("disabled by default", payload.get("enabled") is False, status.stdout)
            )
        except json.JSONDecodeError:
            steps.append(("status command", False, status.stdout + status.stderr))

        enable = run("telemetry", "enable")
        steps.append(("enable", enable.returncode == 0, enable.stderr))

        show = run("telemetry", "show")
        try:
            shown = json.loads(show.stdout)
            # status/enable print a human line before JSON — show should be pure JSON
            forbidden = {"repository_name", "path", "prompt", "finding", "password"}
            steps.append(("show payload", show.returncode == 0, show.stderr))
            steps.append(
                (
                    "payload has installation_id",
                    "installation_id" in shown,
                    show.stdout,
                )
            )
            steps.append(
                ("no forbidden keys", forbidden.isdisjoint(shown), str(list(shown)))
            )
        except json.JSONDecodeError:
            steps.append(("show payload", False, show.stdout + show.stderr))

        disable = run("telemetry", "disable")
        steps.append(("disable", disable.returncode == 0, disable.stderr))
        reset = run("telemetry", "reset")
        steps.append(("reset", reset.returncode == 0, reset.stderr))

        offline = subprocess.run(
            [
                py,
                "-c",
                (
                    "from pathlib import Path;"
                    "from codestrata.telemetry.service import TelemetryService;"
                    "from codestrata.telemetry.constants import EventName;"
                    f"s=TelemetryService(home=Path({str(home)!r}));"
                    "s.enable();"
                    "s.emit(EventName.ASSESSMENT_COMPLETED, command='assess', success=True);"
                    "print(int(s.status()['queue_depth']))"
                ),
            ],
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        queued = offline.stdout.strip().isdigit() and int(offline.stdout.strip()) >= 1
        steps.append(
            ("offline queue", offline.returncode == 0 and queued, offline.stderr)
        )

        failed = False
        for name, ok, detail in steps:
            print(f"{'PASS' if ok else 'FAIL'}: {name}")
            if not ok:
                failed = True
                if detail.strip():
                    print(detail.strip()[:500])
        if failed:
            return 1
        print("DOGFOOD PASS")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
