"""Cloudflare settings contract vs DEPLOYMENT.md."""

from __future__ import annotations

from verification.documentation_deployment.contract import (
    ASSETS_DIR,
    DOCS_ROOT,
    VITEPRESS_OUT,
    WRANGLER_CONFIG,
)
from verification.documentation_deployment.inventory import DeploymentInventory
from verification.documentation_deployment.models import CheckResult

EXPECTED_TABLE = (
    ("Repository root / project root", DOCS_ROOT),
    ("Install command", "npm ci"),
    ("Build command", "npm run build"),
    ("Build output directory", VITEPRESS_OUT),
    ("Deploy command", "npm run deploy:upload"),
    ("Wrangler config", WRANGLER_CONFIG),
    ("Node version", "22+"),
)


def check_cloudflare_settings(inv: DeploymentInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    doc = inv.deployment_md_excerpt

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "cloudflare_settings"))

    for label, value in EXPECTED_TABLE:
        slug = label.lower().replace(" ", "_").replace("/", "_")
        add(
            f"cloudflare_settings:{slug}",
            value in doc,
            value,
        )

    add(
        "cloudflare_settings:assets_directory",
        ASSETS_DIR in doc,
        ASSETS_DIR,
    )
    add(
        "cloudflare_settings:static_assets_mode",
        inv.policy.get("hosting_mode") == "static_assets",
        "static_assets",
    )
    add(
        "cloudflare_settings:no_worker_main",
        inv.policy.get("worker_runtime", {}).get("main_entrypoint_required") is False,
        "false",
    )
    return checks
