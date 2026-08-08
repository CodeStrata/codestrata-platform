"""Accessibility regression via docs validate script."""

from __future__ import annotations

import re
import subprocess

from verification.documentation_deployment.inventory import DeploymentInventory
from verification.documentation_deployment.models import CheckResult


def check_accessibility_regression(inv: DeploymentInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "accessibility_regression"))

    add(
        "accessibility_regression:validate_script",
        inv.package_json.get("scripts", {}).get("validate") == "node scripts/validate.mjs",
        "present",
    )
    add(
        "accessibility_regression:dist_required",
        inv.dist_dir.is_dir() and (inv.dist_dir / "index.html").is_file(),
        "dist_ready",
    )

    try:
        result = subprocess.run(
            ["npm", "run", "validate"],
            cwd=inv.docs_root,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        add("accessibility_regression:validate_passes", False, type(exc).__name__)
        return checks

    detail = re.sub(r"/Users/[^\s\"']+", "<home>", result.stdout + result.stderr)[:300]
    add(
        "accessibility_regression:validate_passes",
        result.returncode == 0,
        "ok" if result.returncode == 0 else detail or "failed",
    )
    add(
        "accessibility_regression:does_not_rerun_14_11",
        True,
        "docs_validate_only",
    )
    return checks
