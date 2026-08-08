"""Package-level validation (Python, VS Code, Insights, Docs, Terraform)."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from verification.repository_package_release_validation.contract import VERSION_ANCHORS
from verification.repository_package_release_validation.helpers import add_check
from verification.repository_package_release_validation.models import CheckResult, Defect


def check_packages(
    roots: dict[str, Path],
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict = {}

    engine = roots.get("codestrata-engine")
    if engine and engine.is_dir():
        py = engine / "pyproject.toml"
        add_check(checks, defects, "package:engine_pyproject", py.is_file(), "pyproject.toml", "package")
        if py.is_file():
            data = tomllib.loads(py.read_text(encoding="utf-8"))
            ver = data.get("project", {}).get("version", "")
            add_check(
                checks,
                defects,
                "package:engine_version",
                ver == VERSION_ANCHORS["engine_cli"],
                ver,
                "package",
            )
            summary["python"] = {"version": ver}
        # no dist/ included
        add_check(
            checks,
            defects,
            "package:engine_no_dist",
            not (engine / "dist").exists(),
            "dist absent",
            "package",
        )

    vs = roots.get("codestrata-vscode")
    if vs and vs.is_dir():
        pkg = vs / "package.json"
        add_check(checks, defects, "package:vscode_manifest", pkg.is_file(), "package.json", "package")
        if pkg.is_file():
            data = json.loads(pkg.read_text(encoding="utf-8"))
            ver = str(data.get("version", ""))
            add_check(
                checks,
                defects,
                "package:vscode_version",
                ver == VERSION_ANCHORS["vscode"],
                ver,
                "package",
            )
            add_check(
                checks,
                defects,
                "package:vscode_icon",
                bool(data.get("icon")) and (vs / str(data.get("icon"))).is_file(),
                str(data.get("icon")),
                "package",
            )
            summary["vscode"] = {"version": ver, "icon": data.get("icon")}
        add_check(
            checks,
            defects,
            "package:vscode_no_vsix_in_export",
            not any(vs.glob("*.vsix")),
            "no vsix residue",
            "package",
        )

    insights = roots.get("codestrata-insights")
    if insights and insights.is_dir():
        pkg = insights / "package.json"
        add_check(checks, defects, "package:insights_manifest", pkg.is_file(), "package.json", "package")
        if pkg.is_file():
            data = json.loads(pkg.read_text(encoding="utf-8"))
            scripts = data.get("scripts") or {}
            for s in ("build", "typecheck", "test"):
                add_check(
                    checks,
                    defects,
                    f"package:insights_script:{s}",
                    s in scripts,
                    s,
                    "package",
                )
            deps = {**(data.get("dependencies") or {}), **(data.get("devDependencies") or {})}
            add_check(
                checks,
                defects,
                "package:insights_no_chart",
                not any(x in {k.lower() for k in deps} for x in ("chart.js", "recharts")),
                "no chart lib",
                "package",
            )
            summary["insights"] = {"scripts": sorted(scripts)}
        add_check(
            checks,
            defects,
            "package:insights_no_dist",
            not (insights / "dist").exists(),
            "dist absent",
            "package",
        )

    docs = roots.get("codestrata-docs")
    if docs and docs.is_dir():
        pkg = docs / "package.json"
        add_check(checks, defects, "package:docs_manifest", pkg.is_file(), "package.json", "package")
        if pkg.is_file():
            data = json.loads(pkg.read_text(encoding="utf-8"))
            scripts = data.get("scripts") or {}
            add_check(checks, defects, "package:docs_build_script", "build" in scripts, "build", "package")
            summary["docs"] = {"scripts": sorted(scripts)}
        add_check(
            checks,
            defects,
            "package:docs_tokens_packaged",
            (docs / "public/design-tokens/tokens.css").is_file()
            or any(docs.rglob("**/design-tokens/tokens.css")),
            "design-tokens",
            "package",
        )

    infra = roots.get("codestrata-infrastructure")
    if infra and infra.is_dir():
        locks = list(infra.rglob(".terraform.lock.hcl"))
        add_check(
            checks,
            defects,
            "package:infra_lockfiles_present",
            bool(locks),
            f"locks={len(locks)}",
            "package",
        )
        add_check(
            checks,
            defects,
            "package:infra_no_tfstate",
            not any(infra.rglob("*.tfstate")),
            "no tfstate",
            "package",
        )
        summary["terraform"] = {"lockfiles": len(locks)}

    return checks, defects, summary
