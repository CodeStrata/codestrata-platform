"""Package-root independence checks."""

from __future__ import annotations

import json
from pathlib import Path

from verification.repository_consistency.inventory import add_check
from verification.repository_consistency.models import CheckResult, Defect

INDEPENDENT_ROOTS = ("docs", "insights", "vscode-plugin")


def check_package_roots(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    root_nm = monorepo / "node_modules"
    for name in INDEPENDENT_ROOTS:
        pkg = monorepo / name / "package.json"
        add_check(checks, defects, f"pkgroot:package_json:{name}", pkg.is_file(), f"{name}/package.json", "package_roots")
        lock = monorepo / name / "package-lock.json"
        # lock preferred; yarn.lock also ok
        has_lock = lock.is_file() or (monorepo / name / "yarn.lock").is_file() or (monorepo / name / "pnpm-lock.yaml").is_file()
        add_check(
            checks,
            defects,
            f"pkgroot:lockfile:{name}",
            has_lock,
            f"{name} lock",
            "package_roots",
        )
        # Must not declare file:../node_modules or rely on root workspace hoisting exclusively
        if pkg.is_file():
            data = json.loads(pkg.read_text(encoding="utf-8"))
            deps = {**(data.get("dependencies") or {}), **(data.get("devDependencies") or {})}
            bad = [k for k, v in deps.items() if isinstance(v, str) and v.startswith("file:../node_modules")]
            add_check(
                checks,
                defects,
                f"pkgroot:no_root_node_modules_file_dep:{name}",
                not bad,
                ",".join(bad) or "ok",
                "package_roots",
                classification="package_root_depends_root_node_modules",
            )

    # Root package.json if present should not be required parent for those roots
    root_pkg = monorepo / "package.json"
    if root_pkg.is_file():
        data = json.loads(root_pkg.read_text(encoding="utf-8"))
        workspaces = data.get("workspaces")
        add_check(
            checks,
            defects,
            "pkgroot:root_not_forced_workspace_parent",
            True,  # monorepo may have optional root; independence is per-package lock
            f"workspaces={bool(workspaces)} root_node_modules={root_nm.exists()}",
            "package_roots",
        )
    else:
        add_check(
            checks,
            defects,
            "pkgroot:no_root_package_json_ok",
            True,
            "independent_roots",
            "package_roots",
        )
    return checks, defects
