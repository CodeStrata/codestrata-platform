"""Build ownership (Approach A) checks."""

from __future__ import annotations

from verification.documentation_deployment.inventory import DeploymentInventory
from verification.documentation_deployment.models import CheckResult


def check_build_ownership(inv: DeploymentInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    scripts = inv.package_json.get("scripts", {})

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "build_ownership"))

    deploy_upload = scripts.get("deploy:upload", "")
    deploy = scripts.get("deploy", "")
    deploy_local = scripts.get("deploy:local", "")
    build = scripts.get("build", "")

    add(
        "build_ownership:build_vitepress_only",
        isinstance(build, str) and build.strip() == "vitepress build",
        str(build),
    )
    add(
        "build_ownership:deploy_upload_no_build",
        isinstance(deploy_upload, str) and "build" not in deploy_upload.lower(),
        str(deploy_upload),
    )
    add(
        "build_ownership:deploy_no_build",
        isinstance(deploy, str) and "npm run build" not in deploy,
        str(deploy),
    )
    add(
        "build_ownership:deploy_local_may_build",
        isinstance(deploy_local, str) and "npm run build" in deploy_local,
        "convenience",
    )
    add(
        "build_ownership:deploy_aliases_upload",
        deploy == "npm run deploy:upload",
        str(deploy),
    )
    return checks
