"""Output alignment regression checks (v0.1.0 failure class)."""

from __future__ import annotations

from pathlib import Path

from verification.documentation_deployment.contract import ASSETS_DIR, VITEPRESS_OUT
from verification.documentation_deployment.inventory import DeploymentInventory
from verification.documentation_deployment.models import CheckResult


def compare_configured_vs_actual(docs_root: Path, assets_directory: str) -> tuple[bool, str]:
    """Return (aligned, detail) comparing wrangler assets.directory to VitePress output."""
    normalized = assets_directory.replace("\\", "/").lstrip("./")
    if normalized in {"docs/.vitepress/dist", "./docs/.vitepress/dist"}:
        return False, "monorepo_relative_path"
    if normalized.endswith("/docs/.vitepress/dist"):
        return False, "monorepo_relative_suffix"

    resolved_assets = (docs_root / assets_directory).resolve()
    vitepress_out = (docs_root / VITEPRESS_OUT).resolve()
    if resolved_assets == vitepress_out:
        return True, VITEPRESS_OUT
    return False, "mismatch"


def check_output_alignment(inv: DeploymentInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    config_dir = inv.wrangler_config.get("assets", {}).get("directory", "")

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "output_alignment"))

    wrong_paths = (
        "docs/.vitepress/dist",
        "./docs/.vitepress/dist",
    )
    add(
        "output_alignment:not_monorepo_docs_path",
        config_dir not in wrong_paths and not str(config_dir).endswith("/docs/.vitepress/dist"),
        str(config_dir or "missing"),
    )
    add(
        "output_alignment:exact_package_relative",
        config_dir in {ASSETS_DIR, ".vitepress/dist", "./.vitepress/dist"},
        str(config_dir),
    )

    aligned, detail = compare_configured_vs_actual(inv.docs_root, str(config_dir))
    add("output_alignment:configured_vs_actual", aligned, detail)

    add(
        "output_alignment:deploy_check_guard",
        "docs/.vitepress/dist" in inv.deploy_check_text
        and "v0.1.0 failure class" in inv.deploy_check_text,
        "guarded",
    )
    return checks
