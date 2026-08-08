"""Security scans for credentials in docs deployment surface."""

from __future__ import annotations

import re

from verification.documentation_deployment.inventory import DeploymentInventory
from verification.documentation_deployment.models import CheckResult

SECRET_PATTERNS = (
    re.compile(r"CLOUDFLARE_API_TOKEN\s*[:=]\s*['\"]?\w{10,}"),
    re.compile(r"CF_API_TOKEN\s*[:=]\s*['\"]?\w{10,}"),
    re.compile(r"api_token\s*[:=]\s*['\"][a-zA-Z0-9_-]{20,}['\"]"),
)


def check_security(inv: DeploymentInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    haystacks = {
        "wrangler.jsonc": inv.wrangler_config_text,
        "package.json": str(inv.package_json),
        "deploy-check.mjs": inv.deploy_check_text,
    }

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "security"))

    leaks: list[str] = []
    for label, text in haystacks.items():
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                leaks.append(label)

    add(
        "security:no_credentials_in_source",
        not leaks,
        "clean" if not leaks else leaks[0],
    )
    add(
        "security:policy_forbids_credentials",
        inv.policy.get("credentials_in_source_allowed") is False,
        "forbidden",
    )
    add(
        "security:deployment_md_secrets_cloudflare_only",
        "Cloudflare environment only" in inv.deployment_md_excerpt,
        "documented",
    )
    return checks
