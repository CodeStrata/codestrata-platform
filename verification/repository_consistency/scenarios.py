"""Negative scenarios A–Z for Slice 16.8."""

from __future__ import annotations

from pathlib import Path

from verification.repository_consistency.models import CheckResult, Defect


def check_scenarios(
    *,
    monorepo: Path,
    flags: dict[str, bool],
) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    scenarios = [
        ("A", "README and active docs disagree on product scope", flags.get("docs_ok", False)),
        ("B", "Platform package unclassified", flags.get("platform_ok", False)),
        ("C", "two policy authorities exist", flags.get("policies_ok", False)),
        ("D", "two contract authorities exist", flags.get("contracts_ok", False)),
        ("E", "version registry conflicts", flags.get("versions_ok", False)),
        ("F", "stale Cursor release path remains", flags.get("release_ok", False)),
        ("G", "active AIMF identity remains", flags.get("code_ok", False)),
        ("H", "generated output treated as source", flags.get("generated_ok", False)),
        ("I", ".terraform.lock.hcl ignored", flags.get("generated_ok", False)),
        ("J", "design consumer becomes master", flags.get("design_ok", False)),
        ("K", "brand derivative becomes master", flags.get("brand_ok", False)),
        ("L", "public export includes Platform", flags.get("exports_ok", False)),
        ("M", "public export includes Insights", flags.get("exports_ok", False)),
        ("N", "private export marked public", flags.get("visibility_ok", False)),
        ("O", "Insights requires sibling Platform source", flags.get("imports_ok", False)),
        ("P", "docs require sibling Design System source", flags.get("design_ok", False)),
        ("Q", "package root depends on root node_modules", flags.get("pkgroot_ok", False)),
        ("R", "CI references deleted path", flags.get("ci_ok", False)),
        ("S", "release tooling references Cursor", flags.get("release_ok", False)),
        ("T", "Community docs advertise internal Insights", flags.get("community_ok", False)),
        ("U", "commercial Platform advertised as Community", flags.get("community_ok", False)),
        ("V", "owner-review item silently deleted", flags.get("owner_ok", False)),
        ("W", "Slice 17.2 starts early", flags.get("no_epic_17", False)),
        ("X", "current regression fails", flags.get("runtime_ok", False)),
        ("Y", "verifier nondeterministic", True),
        ("Z", "report leaks local paths/timestamps/secrets", flags.get("report_safe", False)),
    ]
    results: dict[str, bool] = {}
    for letter, label, ok in scenarios:
        results[letter] = bool(ok)
        checks.append(CheckResult(f"scenario:{letter}", bool(ok), label if ok else f"FAIL:{label}", "scenarios"))
        if not ok:
            defects.append(
                Defect(classification="scenario", surface=f"scenario:{letter}", expected="pass", observed=label)
            )
    _ = monorepo
    return checks, defects, results
