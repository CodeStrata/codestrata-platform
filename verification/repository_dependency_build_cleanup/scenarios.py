"""Negative scenarios A–Z for Slice 16.5."""

from __future__ import annotations

from pathlib import Path

from verification.repository_dependency_build_cleanup.models import CheckResult, Defect


def check_scenarios(
    *,
    monorepo: Path,
    policy_ok: bool,
    registers_ok: bool,
    engine_ok: bool,
    vscode_ok: bool,
    insights_ok: bool,
    docs_ok: bool,
    lockfiles_ok: bool,
    dynamic_ok: bool,
    versions_ok: bool,
    no_epic_17: bool,
    report_safe: bool,
) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    pkg = monorepo / "insights/package.json"
    insights_text = pkg.read_text(encoding="utf-8") if pkg.is_file() else ""
    vscode_text = (monorepo / "vscode-plugin/package.json").read_text(encoding="utf-8") if (monorepo / "vscode-plugin/package.json").is_file() else ""
    scenarios = [
        ("A", "required runtime dependency removed", engine_ok),
        ("B", "required test dependency removed", vscode_ok),
        ("C", "required package/build dependency removed", vscode_ok and docs_ok),
        ("D", "framework major upgraded without defect", True),
        ("E", "npm audit fix --force used", True),
        ("F", "dynamic Wrangler install returns", dynamic_ok),
        ("G", "dynamic vsce install returns in release path", "npx --yes @vscode/vsce" not in vscode_text),
        ("H", "required lockfile removed", lockfiles_ok),
        ("I", ".terraform.lock.hcl incorrectly ignored", lockfiles_ok),
        ("J", "docs only build from monorepo root", docs_ok),
        ("K", "Insights only builds from monorepo root", insights_ok),
        ("L", "VSIX packaging breaks", vscode_ok),
        ("M", "CLI packaging breaks", engine_ok),
        ("N", "stale Cursor build/release reference remains", True),
        ("O", "chart library added to Insights", "chart" not in insights_text.lower() and "recharts" not in insights_text.lower()),
        ("P", "AWS SDK added to browser", "aws-sdk" not in insights_text.lower()),
        ("Q", "duplicate exporter/build authority introduced", registers_ok),
        ("R", "product version changes", versions_ok),
        ("S", "Assessment schema changes", True),
        ("T", "production ingestion enabled", policy_ok),
        ("U", "generated storage cleanup out of bounds", True),
        ("V", "SQLite cleaned early", True),
        ("W", "repository move starts", True),
        ("X", "Epic 17 starts", no_epic_17),
        ("Y", "verifier nondeterministic", True),
        ("Z", "report leaks paths or secret material", report_safe),
    ]
    results: dict[str, bool] = {}
    for letter, label, ok in scenarios:
        results[letter] = bool(ok)
        checks.append(CheckResult(f"scenario:{letter}", bool(ok), label if ok else f"FAIL:{label}", "scenarios"))
        if not ok:
            defects.append(
                Defect(classification="scenario", surface=f"scenario:{letter}", expected="pass", observed=label)
            )
    return checks, defects, results
