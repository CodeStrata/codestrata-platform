"""Dependency and build authority consistency."""

from __future__ import annotations

import json
from pathlib import Path

from verification.repository_consistency.inventory import add_check, load_json
from verification.repository_consistency.models import CheckResult, Defect

DEP_REG = "platform/policies/repository_dependency_register.json"
BUILD_REG = "platform/policies/repository_build_authority_register.json"


def check_dependencies(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / DEP_REG
    add_check(checks, defects, "deps:register_exists", path.is_file(), DEP_REG, "dependencies")
    if path.is_file():
        data = load_json(path)
        add_check(
            checks,
            defects,
            "deps:schema",
            "dependency" in str(data.get("schema", "")).lower(),
            str(data.get("schema")),
            "dependencies",
        )

    # Insights: no chart dependency
    insights_pkg = monorepo / "insights/package.json"
    if insights_pkg.is_file():
        blob = insights_pkg.read_text(encoding="utf-8").lower()
        charts = ["chart.js", "recharts", "victory", "nivo", "highcharts"]
        hit = [c for c in charts if c in blob]
        add_check(
            checks,
            defects,
            "deps:insights_no_chart",
            not hit,
            ",".join(hit) or "none",
            "dependencies",
        )
        add_check(
            checks,
            defects,
            "deps:insights_no_aws_sdk",
            "@aws-sdk" not in blob,
            "aws-sdk",
            "dependencies",
        )

    # Docs/VS Code: no AWS SDK in browser package.json
    for rel in ("docs/package.json", "vscode-plugin/package.json"):
        p = monorepo / rel
        if p.is_file():
            blob = p.read_text(encoding="utf-8")
            add_check(
                checks,
                defects,
                f"deps:no_aws_sdk:{rel}",
                "@aws-sdk" not in blob,
                rel,
                "dependencies",
            )

    # No dynamic unpinned release installs in package scripts
    for rel in ("vscode-plugin/package.json", "docs/package.json", "insights/package.json"):
        p = monorepo / rel
        if not p.is_file():
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        scripts = " ".join(str(v) for v in (data.get("scripts") or {}).values())
        bad = "npx --yes" in scripts or "npx -y " in scripts
        add_check(
            checks,
            defects,
            f"deps:no_dynamic_npx:{rel}",
            not bad,
            scripts[:120],
            "dependencies",
        )

    # No Cursor packaging commands
    vs = monorepo / "vscode-plugin/package.json"
    if vs.is_file():
        t = vs.read_text(encoding="utf-8").lower()
        add_check(
            checks,
            defects,
            "deps:no_cursor_packaging",
            "cursor" not in t or "codestrata-cursor" not in t,
            "vscode package",
            "dependencies",
        )
    return checks, defects


def check_builds(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[dict[str, str]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: list[dict[str, str]] = []
    path = monorepo / BUILD_REG
    add_check(checks, defects, "builds:register_exists", path.is_file(), BUILD_REG, "builds")
    if not path.is_file():
        return checks, defects, summary
    data = load_json(path)
    authorities = data.get("authorities", [])
    surfaces: dict[str, int] = {}
    for auth in authorities:
        surface = auth.get("surface", "")
        surfaces[surface] = surfaces.get(surface, 0) + 1
        root = auth.get("package_root", "")
        cmds = auth.get("commands") or []
        summary.append(
            {
                "surface": surface,
                "package_root": root,
                "commands": "; ".join(cmds),
            }
        )
        add_check(
            checks,
            defects,
            f"builds:root_exists:{surface}",
            not root or (monorepo / root).exists() or root.endswith("/"),
            root,
            "builds",
        )
        # package root path
        if root and root.endswith("/"):
            add_check(
                checks,
                defects,
                f"builds:pkg_dir:{surface}",
                (monorepo / root).is_dir() or surface in {"Release verification", "Repository exports", "Brand generation"},
                root,
                "builds",
            )
    for surface, count in surfaces.items():
        add_check(
            checks,
            defects,
            f"builds:unique_surface:{surface}",
            count == 1,
            str(count),
            "builds",
            classification="duplicate_build_authority",
        )
    return checks, defects, summary
