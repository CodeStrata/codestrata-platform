"""Brand asset presence in build output."""

from __future__ import annotations

from verification.documentation_deployment.inventory import DeploymentInventory
from verification.documentation_deployment.models import CheckResult

BRAND_FILES = (
    "brand/lockup-horizontal-on-light.svg",
    "brand/lockup-horizontal-on-dark.svg",
    "brand/icon.svg",
)


def check_assets(inv: DeploymentInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    dist = inv.dist_dir

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "assets"))

    for brand in BRAND_FILES:
        present = (dist / brand).is_file()
        add(f"assets:{brand.replace('/', '_')}", present, "present" if present else "missing")

    add(
        "assets:favicon_root",
        (dist / "favicon.svg").is_file(),
        "present",
    )
    return checks
