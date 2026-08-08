"""Non-interactive deployment configuration checks."""

from __future__ import annotations

from verification.documentation_deployment.inventory import DeploymentInventory
from verification.documentation_deployment.models import CheckResult


def check_non_interactive(inv: DeploymentInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    scripts = inv.package_json.get("scripts", {})

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "non_interactive"))

    add(
        "non_interactive:wrangler_checked_in",
        bool(inv.wrangler_config_text),
        "checked_in",
    )
    add(
        "non_interactive:no_auto_setup_script",
        not any("wrangler init" in str(v) for v in scripts.values()),
        "absent",
    )
    add(
        "non_interactive:no_npx_wrangler",
        not any("npx wrangler" in str(v) for v in scripts.values()),
        "absent",
    )
    add(
        "non_interactive:policy_checked_in",
        inv.policy.get("deployment_configuration_checked_in") is True,
        "true",
    )
    return checks
