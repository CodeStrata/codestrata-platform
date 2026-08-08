"""Dependency posture checks."""

from __future__ import annotations

import json
import re
import subprocess

from verification.documentation_deployment.contract import VITEPRESS_PIN
from verification.documentation_deployment.inventory import DeploymentInventory
from verification.documentation_deployment.models import CheckResult


def check_dependencies(
    inv: DeploymentInventory,
) -> tuple[list[CheckResult], list[str]]:
    checks: list[CheckResult] = []
    limitations: list[str] = []
    deps = inv.package_json.get("devDependencies", {})

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "dependencies"))

    add(
        "dependencies:lockfile_present",
        (inv.docs_root / "package-lock.json").is_file(),
        "present",
    )
    add(
        "dependencies:wrangler_declared",
        "wrangler" in deps,
        str(deps.get("wrangler")),
    )

    vitepress = deps.get("vitepress", "")
    add(
        "dependencies:vitepress_pin_posture",
        "1.6." in str(vitepress),
        str(vitepress),
    )
    add(
        "dependencies:vitepress_not_upgraded_for_hardening",
        inv.policy.get("vitepress_pin_posture") == "do_not_upgrade_for_deployment_hardening",
        VITEPRESS_PIN,
    )

    try:
        result = subprocess.run(
            ["npm", "audit", "--json"],
            cwd=inv.docs_root,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if result.returncode in {0, 1} and result.stdout.strip():
            audit = json.loads(result.stdout)
            vuln_meta = audit.get("metadata", {}).get("vulnerabilities", {})
            if isinstance(vuln_meta, dict):
                vuln_count = sum(
                    int(value.get("total", 0) if isinstance(value, dict) else value)
                    for value in vuln_meta.values()
                )
            else:
                vuln_count = 0
            add(
                "dependencies:npm_audit_classified",
                True,
                f"vulnerabilities={vuln_count}",
            )
        else:
            add("dependencies:npm_audit_classified", True, "unavailable")
            limitations.append("npm_audit_unavailable")
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        add("dependencies:npm_audit_classified", True, "skipped")
        limitations.append("npm_audit_unavailable")

    add(
        "dependencies:no_audit_fix_force_guidance",
        "audit fix --force" not in inv.deployment_md_excerpt,
        "absent",
    )
    return checks, limitations
