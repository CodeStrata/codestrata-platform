"""VitePress configuration checks."""

from __future__ import annotations

from verification.documentation_deployment.inventory import DeploymentInventory
from verification.documentation_deployment.models import CheckResult


def check_vitepress(inv: DeploymentInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    config = inv.vitepress_config_text
    scripts = inv.package_json.get("scripts", {})

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "vitepress"))

    add(
        "vitepress:config_exists",
        bool(config),
        "present" if config else "missing",
    )
    add(
        "vitepress:no_custom_outdir",
        "outDir" not in config,
        "default",
    )
    add(
        "vitepress:build_script",
        isinstance(scripts.get("build"), str) and "vitepress build" in scripts["build"],
        str(scripts.get("build", "")),
    )
    add(
        "vitepress:dist_gitignored",
        ".vitepress/dist/" in inv.gitignore_text or ".vitepress/dist" in inv.gitignore_text,
        "ignored",
    )
    return checks
