"""Preflight deploy:check execution."""

from __future__ import annotations

import re
import subprocess

from verification.documentation_deployment.inventory import DeploymentInventory
from verification.documentation_deployment.models import CheckResult


def _sanitize(text: str) -> str:
    text = re.sub(r"/Users/[^\s\"']+", "<home>", text)
    text = re.sub(r"/home/[^\s\"']+", "<home>", text)
    text = re.sub(r"[A-Za-z]:\\\\[^\s\"']+", "<path>", text)
    return text[:500]


def check_preflight(inv: DeploymentInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "preflight"))

    add(
        "preflight:script_exists",
        bool(inv.deploy_check_text),
        "present" if inv.deploy_check_text else "missing",
    )

    try:
        result = subprocess.run(
            ["npm", "run", "deploy:check"],
            cwd=inv.docs_root,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        add("preflight:deploy_check", False, type(exc).__name__)
        return checks

    combined = _sanitize(result.stdout + result.stderr)
    add(
        "preflight:deploy_check",
        result.returncode == 0,
        "ok" if result.returncode == 0 else combined or "failed",
    )
    add(
        "preflight:package_root_in_output",
        "docs" in result.stdout or result.returncode == 0,
        "docs",
    )
    return checks
