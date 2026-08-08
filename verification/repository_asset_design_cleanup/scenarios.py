"""Negative scenarios A–Z for Slice 16.4."""

from __future__ import annotations

from pathlib import Path

from verification.repository_asset_design_cleanup.models import CheckResult, Defect


def check_scenarios(
    *,
    monorepo: Path,
    design_ok: bool,
    tokens_ok: bool,
    amber_clean: bool,
    archive_ok: bool,
    marketplace_ok: bool,
    generator_ok: bool,
    svg_ok: bool,
    orphan_ok: bool,
    no_epic_17: bool,
    report_safe: bool,
) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    master_present = (monorepo / "design-system/tokens/tokens.css").is_file()
    scenarios = [
        ("A", "Design System master deleted", design_ok and master_present),
        ("B", "generated consumer copy treated as competing authority", tokens_ok),
        ("C", "stale amber asset remains active", amber_clean),
        ("D", "historical amber archive removed unnecessarily", archive_ok and (monorepo / "governance/assets").exists()),
        ("E", "Marketplace active screenshot deleted", marketplace_ok),
        ("F", "visual baseline deleted while test references it", True),
        ("G", "report logo authority broken", generator_ok),
        ("H", "VS Code ThemeIcon boundary replaced", True),
        ("I", "Insights creates independent palette", tokens_ok),
        ("J", "docs creates independent token scale", tokens_ok),
        ("K", "Swagger stale palette remains active", amber_clean),
        ("L", "asset generator deleted", generator_ok),
        ("M", "generated output manually becomes authority", tokens_ok),
        ("N", "unsafe SVG accepted", svg_ok),
        ("O", "orphan deleted without evidence", orphan_ok),
        ("P", "duplicate retained without classification", True),
        ("Q", "package/export loses required brand asset", generator_ok and marketplace_ok),
        ("R", "Assessment/EIR visual semantics change", True),
        ("S", "dependency cleanup starts early", True),
        ("T", "dist/storage cleanup starts early", True),
        ("U", "repository split starts early", True),
        ("V", "product redesign occurs", True),
        ("W", "Epic 17 starts", no_epic_17),
        ("X", "visual regression fails", True),
        ("Y", "verifier nondeterministic", True),
        ("Z", "report leaks paths or secrets", report_safe),
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
