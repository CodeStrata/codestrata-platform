"""Package root model B checks."""

from __future__ import annotations

from verification.documentation_deployment.contract import DOCS_ROOT
from verification.documentation_deployment.inventory import DeploymentInventory
from verification.documentation_deployment.models import CheckResult


def check_package_root(inv: DeploymentInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "package_root"))

    add(
        "package_root:no_monorepo_package_json",
        not (inv.monorepo / "package.json").is_file(),
        "absent",
    )
    add(
        "package_root:docs_package_json",
        (inv.docs_root / "package.json").is_file(),
        "present",
    )
    add(
        "package_root:docs_is_cloudflare_root",
        inv.policy.get("cloudflare_project_root") == DOCS_ROOT,
        DOCS_ROOT,
    )
    add(
        "package_root:wrangler_next_to_package_json",
        (inv.docs_root / "wrangler.jsonc").is_file()
        and (inv.docs_root / "package.json").is_file(),
        "siblings",
    )
    return checks
