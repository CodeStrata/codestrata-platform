"""Release tooling consistency."""

from __future__ import annotations

from pathlib import Path

from verification.repository_consistency.inventory import add_check
from verification.repository_consistency.models import CheckResult, Defect


def check_release_tooling(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    # VS Code only among active editor clients
    add_check(
        checks,
        defects,
        "release:vscode_present",
        (monorepo / "vscode-plugin/package.json").is_file(),
        "vscode-plugin",
        "release_tooling",
    )
    add_check(
        checks,
        defects,
        "release:cursor_absent",
        not (monorepo / "cursor-plugin").exists() and not (monorepo / "codestrata-cursor").exists(),
        "cursor absent",
        "release_tooling",
        classification="cursor_release_path",
    )

    # Scan scripts for Cursor release references as active targets
    scripts = monorepo / "scripts"
    cursor_active = []
    if scripts.is_dir():
        for p in scripts.rglob("*.py"):
            t = p.read_text(encoding="utf-8", errors="ignore").lower()
            if "codestrata-cursor" in t and "retired" not in t and "forbidden" not in t and "removed" not in t:
                # allow prohibited_files lists
                if "prohibited" in t or "retired" in Path(p).read_text(encoding="utf-8", errors="ignore").lower():
                    continue
                if "cursor-plugin/" in t and ("prohibit" in t or "omit" in t or "retired" in t):
                    continue
                # soft: only flag packaging publish scripts
                if "publish" in t and "cursor" in t:
                    cursor_active.append(p.relative_to(monorepo).as_posix())
    add_check(
        checks,
        defects,
        "release:no_cursor_publish_scripts",
        not cursor_active,
        ",".join(cursor_active[:5]) or "ok",
        "release_tooling",
    )

    # Infrastructure/Insights treated private in export policies
    infra_pol = monorepo / "scripts/repository_export/policy.py"
    if infra_pol.is_file():
        t = infra_pol.read_text(encoding="utf-8")
        add_check(
            checks,
            defects,
            "release:infra_private_target",
            'TARGET = "infrastructure"' in t or "TARGET=" in t,
            "infrastructure target",
            "release_tooling",
        )

    insights_pol = monorepo / "scripts/insights_repository_export/policy.py"
    if insights_pol.is_file():
        t = insights_pol.read_text(encoding="utf-8")
        add_check(
            checks,
            defects,
            "release:insights_private_target",
            'TARGET = "insights"' in t,
            "insights target",
            "release_tooling",
        )

    # Versions coherent with anchors
    import json
    import tomllib

    eng = tomllib.loads((monorepo / "engine/pyproject.toml").read_text(encoding="utf-8"))
    vs = json.loads((monorepo / "vscode-plugin/package.json").read_text(encoding="utf-8"))
    add_check(
        checks,
        defects,
        "release:versions_coherent_0_2_0",
        eng.get("project", {}).get("version") == "0.2.0" and vs.get("version") == "0.2.0",
        f"engine={eng.get('project', {}).get('version')} vscode={vs.get('version')}",
        "release_tooling",
    )
    return checks, defects
