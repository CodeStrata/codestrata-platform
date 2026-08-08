"""Wrangler CLI telemetry boundary checks."""

from __future__ import annotations

from verification.documentation_deployment.inventory import DeploymentInventory
from verification.documentation_deployment.models import CheckResult


def check_wrangler_telemetry(inv: DeploymentInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    doc = inv.deployment_md_excerpt

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "wrangler_telemetry"))

    add(
        "wrangler_telemetry:documented_distinction",
        "Cloudflare tooling telemetry" in doc,
        "documented",
    )
    add(
        "wrangler_telemetry:ci_can_disable",
        "WRANGLER_SEND_METRICS=false" in doc,
        "documented",
    )
    add(
        "wrangler_telemetry:not_codestrata_telemetry",
        "CodeStrata consent/contracts are unchanged" in doc,
        "boundary",
    )
    return checks
