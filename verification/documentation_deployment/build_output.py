"""Build output verification."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from verification.documentation_deployment.contract import DOCS_ROOT, VITEPRESS_OUT
from verification.documentation_deployment.inventory import DeploymentInventory
from verification.documentation_deployment.models import CheckResult


def _ensure_dist(inv: DeploymentInventory) -> tuple[bool, str]:
    dist = inv.dist_dir
    if dist.is_dir() and (dist / "index.html").is_file():
        return True, "existing"
    env = os.environ.copy()
    try:
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=inv.docs_root,
            capture_output=True,
            text=True,
            env=env,
            timeout=300,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, type(exc).__name__
    if result.returncode != 0:
        return False, "build_failed"
    return dist.is_dir(), "built"


def check_build_output(inv: DeploymentInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    dist = inv.dist_dir

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "build_output"))

    ok, detail = _ensure_dist(inv)
    add("build_output:dist_exists", ok, detail)

    index_ok = (dist / "index.html").is_file()
    assets_ok = (dist / "assets").is_dir()
    sitemap_ok = (dist / "sitemap.xml").is_file()
    favicon_ok = (dist / "favicon.svg").is_file()

    add("build_output:index_html", index_ok, "present" if index_ok else "missing")
    add("build_output:assets_dir", assets_ok, "present" if assets_ok else "missing")
    add("build_output:sitemap", sitemap_ok, "present" if sitemap_ok else "missing")
    add("build_output:favicon", favicon_ok, "present" if favicon_ok else "missing")
    add(
        "build_output:relative_path",
        str(dist.relative_to(inv.docs_root)).replace("\\", "/") == VITEPRESS_OUT,
        VITEPRESS_OUT,
    )
    return checks
