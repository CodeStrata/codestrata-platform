"""Source mutation boundary around preflight."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from verification.documentation_deployment.inventory import DeploymentInventory
from verification.documentation_deployment.models import CheckResult


def _hash(path: Path) -> str:
    if not path.is_file():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tracked_files(inv: DeploymentInventory) -> dict[str, Path]:
    docs = inv.docs_root
    return {
        "package.json": docs / "package.json",
        "package-lock.json": docs / "package-lock.json",
        ".gitignore": docs / ".gitignore",
        "wrangler.jsonc": docs / "wrangler.jsonc",
        "vitepress_config.ts": docs / ".vitepress" / "config.ts",
    }


def check_mutation_boundary(inv: DeploymentInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    files = _tracked_files(inv)
    before = {name: _hash(path) for name, path in files.items()}

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "mutation_boundary"))

    add(
        "mutation_boundary:snapshot_before",
        all(before.values()),
        f"{len(before)}_files",
    )

    try:
        subprocess.run(
            ["npm", "run", "deploy:check"],
            cwd=inv.docs_root,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        add("mutation_boundary:unchanged_after_preflight", False, "preflight_error")
        return checks

    after = {name: _hash(path) for name, path in files.items()}
    unchanged = before == after
    add(
        "mutation_boundary:unchanged_after_preflight",
        unchanged,
        "unchanged" if unchanged else "mutated",
    )
    return checks
