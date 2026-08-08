"""Public/private visibility matrix."""

from __future__ import annotations

from pathlib import Path

from verification.repository_consistency.inventory import add_check, load_json
from verification.repository_consistency.models import CheckResult, Defect

RESIDENCY = "platform/policies/repository_residency_map.json"

EXPECTED = {
    "engine": "public_community",
    "platform": "private",
    "infrastructure": "private",
    "insights": "private_internal",
    "docs": "public",
    "vscode": "public_marketplace",
    "verification": "private_engineering",
}


def check_visibility(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[dict[str, str]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    matrix: list[dict[str, str]] = []
    path = monorepo / RESIDENCY
    add_check(checks, defects, "visibility:map_exists", path.is_file(), RESIDENCY, "visibility")
    if not path.is_file():
        return checks, defects, matrix
    data = load_json(path)
    by_comp = {e.get("component"): e for e in data.get("entries", [])}
    for comp, expected_vis in EXPECTED.items():
        entry = by_comp.get(comp, {})
        vis = str(entry.get("visibility", ""))
        ok = expected_vis in vis or vis == expected_vis
        # docs may be "public" exactly
        if comp == "docs":
            ok = vis.startswith("public")
        if comp == "infrastructure":
            ok = vis.startswith("private")
        if comp == "platform":
            ok = vis.startswith("private")
        add_check(
            checks,
            defects,
            f"visibility:{comp}",
            ok,
            vis,
            "visibility",
            classification="visibility_mismatch",
        )
        matrix.append(
            {
                "component": comp,
                "visibility": vis,
                "export_target": str(entry.get("export_target")),
                "expected": expected_vis,
            }
        )

    # Platform must not have public community export_target
    plat = by_comp.get("platform", {})
    add_check(
        checks,
        defects,
        "visibility:platform_no_public_export",
        plat.get("export_target") in {None, "null", ""} or plat.get("export_target") is None,
        str(plat.get("export_target")),
        "visibility",
    )
    return checks, defects, matrix
