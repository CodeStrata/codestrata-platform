"""Wrangler configuration checks."""

from __future__ import annotations

from verification.documentation_deployment.contract import ASSETS_DIR, WRANGLER_VERSION
from verification.documentation_deployment.inventory import DeploymentInventory
from verification.documentation_deployment.models import CheckResult


def check_wrangler(inv: DeploymentInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    config = inv.wrangler_config
    pkg = inv.package_json
    scripts = pkg.get("scripts", {})
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "wrangler"))

    add(
        "wrangler:config_present",
        bool(config),
        "present" if config else "missing",
    )
    add(
        "wrangler:name",
        config.get("name") == "codestrata-docs",
        str(config.get("name")),
    )
    add(
        "wrangler:assets_directory",
        config.get("assets", {}).get("directory") == ASSETS_DIR,
        str(config.get("assets", {}).get("directory")),
    )
    add("wrangler:no_main", "main" not in config, "absent")
    add(
        "wrangler:no_nodejs_compat",
        "nodejs_compat" not in (config.get("compatibility_flags") or []),
        "absent",
    )
    add(
        "wrangler:local_dependency_declared",
        "wrangler" in deps,
        deps.get("wrangler", "missing"),
    )
    add(
        "wrangler:local_dependency_pinned",
        deps.get("wrangler") == WRANGLER_VERSION,
        str(deps.get("wrangler")),
    )
    add(
        "wrangler:local_dependency_installed",
        inv.local_wrangler_version == WRANGLER_VERSION,
        str(inv.local_wrangler_version or "missing"),
    )
    add(
        "wrangler:no_npx_in_scripts",
        not any("npx wrangler" in str(v) for v in scripts.values()),
        "absent",
    )
    add(
        "wrangler:deploy_upload_uses_local",
        isinstance(scripts.get("deploy:upload"), str)
        and scripts["deploy:upload"].strip() == "wrangler deploy",
        str(scripts.get("deploy:upload", "")),
    )
    return checks
