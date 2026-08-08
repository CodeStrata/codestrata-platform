"""Cross-surface consistency boundary checks."""

from __future__ import annotations

from verification.responsive_accessibility.contract import FORBIDDEN_EPIC_15_PATHS
from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "consistency_boundary"


def check_consistency_boundary(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    expected = inv.policy.get("expected_unchanged", {})
    html = inv.assessment_html

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    add(
        "consistency_boundary:design_system_version",
        expected.get("design_system_version") == "1.0",
        str(expected.get("design_system_version")),
    )
    add(
        "consistency_boundary:assessment_ia_cover",
        'id="cover"' in html,
        "cover",
    )
    add(
        "consistency_boundary:assessment_ia_contents",
        'id="contents"' in html or "Contents" in html,
        "contents",
    )
    add(
        "consistency_boundary:assessment_executive_summary",
        "executive-summary" in html.lower() or 'id="executive-summary"' in html,
        "executive",
    )
    add(
        "consistency_boundary:severity_shape_markers",
        "severity-" in inv.assessment_styles and "::before" in inv.assessment_styles,
        "shapes",
    )
    add(
        "consistency_boundary:mark_viewbox",
        'viewBox="0 0 22 22"' in inv.assessment_html
        and 'viewBox="0 0 22 22"' in inv.eir_html,
        "22x22",
    )
    add(
        "consistency_boundary:extension_version",
        inv.vscode_package.get("version") == "0.2.0",
        str(inv.vscode_package.get("version")),
    )

    markers = [path for path in FORBIDDEN_EPIC_15_PATHS if (inv.monorepo / path).exists()]
    add(
        "consistency_boundary:no_slice_14_14_markers",
        not markers,
        "absent",
    )

    if any(not c.ok for c in checks):
        defects.append(Defect("consistency_boundary", "prior slice contracts were altered"))
    return checks, defects
