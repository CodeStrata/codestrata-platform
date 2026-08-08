"""Clean CI posture checks."""

from __future__ import annotations

from verification.documentation_deployment.inventory import DeploymentInventory
from verification.documentation_deployment.models import CheckResult


def check_clean_ci(inv: DeploymentInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    scripts = inv.package_json.get("scripts", {})

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "clean_ci"))

    add(
        "clean_ci:package_lock_present",
        (inv.docs_root / "package-lock.json").is_file(),
        "present",
    )
    add(
        "clean_ci:deploy_check_script",
        "deploy:check" in scripts,
        "present",
    )
    add(
        "clean_ci:install_command_documented",
        "npm ci" in inv.deployment_md_excerpt,
        "npm ci",
    )
    add(
        "clean_ci:local_wrangler_after_install",
        inv.local_wrangler_version is not None,
        str(inv.local_wrangler_version or "missing"),
    )
    add(
        "clean_ci:integration_note",
        True,
        "full_temp_npm_ci_integration_gated",
    )
    return checks
