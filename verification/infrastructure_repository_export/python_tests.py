"""Exported-repository Python test execution."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from verification.infrastructure_repository_export.models import CheckResult, Defect

_TIMEOUT = 300

# Scrub AWS + avoid leaking monorepo into PYTHONPATH
_SCRUB_KEYS = (
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AWS_PROFILE",
    "AWS_DEFAULT_PROFILE",
    "AWS_WEB_IDENTITY_TOKEN_FILE",
    "AWS_SHARED_CREDENTIALS_FILE",
    "AWS_CONFIG_FILE",
)


def _scrubbed_env(*, export_root: Path) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in _SCRUB_KEYS}
    env["AWS_EC2_METADATA_DISABLED"] = "true"
    env["AWS_REGION"] = "us-east-1"
    # Do not inherit monorepo PYTHONPATH; set only export root
    env["PYTHONPATH"] = str(export_root)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def run_exported_pytest(export_root: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    python = sys.executable
    cmd = [
        python,
        "-m",
        "pytest",
        "-q",
        "tests",
        "--override-ini=cache_dir=.pytest_cache",
    ]
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(export_root),
            env=_scrubbed_env(export_root=export_root),
            capture_output=True,
            text=True,
            check=False,
            timeout=_TIMEOUT,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return (
            [CheckResult("python:tests_timeout", False, "timeout", "python")],
            [Defect("exported-test defect", "pytest", "pass", "timeout")],
        )

    ok = completed.returncode == 0
    # Bounded detail only
    detail = "pass" if ok else f"exit={completed.returncode}"
    checks.append(CheckResult("python:pytest_tests", ok, detail, "python"))
    if not ok:
        # Classify: dependency vs assertion — keep bounded
        stderr = (completed.stderr or "") + (completed.stdout or "")
        if "ModuleNotFoundError" in stderr or "ImportError" in stderr:
            if "codestrata" in stderr or "codestrata_platform" in stderr:
                defects.append(
                    Defect(
                        "exported-test defect",
                        "pytest",
                        "no_engine_platform",
                        "runtime_import",
                    )
                )
            else:
                defects.append(
                    Defect("exported-test defect", "pytest", "pass", "import_error")
                )
        else:
            defects.append(Defect("exported-test defect", "pytest", "pass", "failed"))
    return checks, defects
