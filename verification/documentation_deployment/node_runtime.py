"""Node runtime engine checks."""

from __future__ import annotations

from verification.documentation_deployment.inventory import DeploymentInventory
from verification.documentation_deployment.models import CheckResult


def check_node_runtime(inv: DeploymentInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    engines = inv.package_json.get("engines", {})

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "node_runtime"))

    add(
        "node_runtime:engines_node",
        engines.get("node") == ">=22",
        str(engines.get("node")),
    )
    add(
        "node_runtime:policy_match",
        inv.policy.get("node_engines") == engines.get("node") == ">=22",
        ">=22",
    )
    add(
        "node_runtime:deployment_md_documents",
        ">=22" in inv.deployment_md_excerpt,
        "documented",
    )
    return checks
