"""Status and severity visualization checks."""

from __future__ import annotations

from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "status_visualization"


def check_status_visualization(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    add(
        "status_visualization:assessment_shape_markers",
        "severity-" in inv.assessment_styles and "::before" in inv.assessment_styles,
        "before_pseudo",
    )
    add(
        "status_visualization:eir_shape_markers",
        "status-severity" in inv.eir_styles and "::before" in inv.eir_styles,
        "before_pseudo",
    )
    add(
        "status_visualization:assessment_text_badges",
        "severity-critical" in inv.assessment_html
        or 'sr-only">Severity' in inv.assessment_html,
        "textual",
    )
    add(
        "status_visualization:eir_text_badges",
        'sr-only">Severity' in inv.eir_html or "status-severity" in inv.eir_html,
        "textual",
    )

    has_confidence = "confidence" in inv.eir_html.lower()
    add(
        "status_visualization:eir_confidence_text",
        not has_confidence
        or ("confidence-badge" in inv.eir_html and "confidence" in inv.eir_html.lower()),
        "badge" if has_confidence else "absent",
    )

    print_css = inv.assessment_styles + inv.eir_styles
    add(
        "status_visualization:print_badge_ink",
        "@media print" in print_css
        and (".status-badge" in print_css or ".badge" in print_css)
        and "border:" in print_css,
        "print_ink",
    )

    if any(not c.ok for c in checks):
        defects.append(Defect("status_visualization", "status is conveyed by color alone"))
    return checks, defects
