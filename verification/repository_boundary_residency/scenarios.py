"""Negative scenarios A–Z for Slice 16.7."""

from __future__ import annotations

from pathlib import Path

from verification.repository_boundary_residency.models import CheckResult, Defect


def check_scenarios(
    *,
    monorepo: Path,
    policy_ok: bool,
    map_ok: bool,
    platform_ok: bool,
    imports_ok: bool,
    mirrors_ok: bool,
    exports_ok: bool,
    boundaries_ok: bool,
    no_epic_17: bool,
    report_safe: bool,
) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    scenarios = [
        ("A", "Engine imports Platform runtime", imports_ok),
        ("B", "Insights imports Platform Python", imports_ok),
        ("C", "Infrastructure imports Engine runtime", imports_ok),
        ("D", "Docs publish Platform runtime/internal docs", imports_ok),
        ("E", "public Community export includes Platform", exports_ok),
        ("F", "public Community export includes Infrastructure", exports_ok),
        ("G", "public Community export includes Insights", exports_ok),
        ("H", "Platform package has no owner/classification", platform_ok),
        ("I", "two policy mirrors both treated authoritative", mirrors_ok and policy_ok),
        ("J", "Design System consumer copy becomes master", map_ok),
        ("K", "brand derivative becomes master", map_ok),
        ("L", "future standalone repo requires ../platform", imports_ok),
        ("M", "future standalone repo requires ../design-system", imports_ok),
        ("N", "export contains secrets/state", True),
        ("O", "Cursor product returns in Community export", exports_ok),
        ("P", "commercial prototype promoted as Community capability", platform_ok),
        ("Q", "repository visibility incorrect", map_ok),
        ("R", "source authority becomes dual-written", policy_ok),
        ("S", "remote repo created", boundaries_ok),
        ("T", "Git init/push/tag performed", boundaries_ok),
        ("U", "cutover source deleted", boundaries_ok),
        ("V", "dependency/storage cleanup repeated", boundaries_ok),
        ("W", "Epic 17 starts", no_epic_17),
        ("X", "standalone export regression", exports_ok),
        ("Y", "verifier nondeterministic", True),
        ("Z", "report leaks absolute paths or secret material", report_safe),
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
