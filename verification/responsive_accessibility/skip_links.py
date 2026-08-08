"""Skip navigation link checks."""

from __future__ import annotations

from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "skip_link"


def check_skip_links(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    add(
        "skip_link:assessment_href",
        'href="#main-content"' in inv.assessment_html,
        "main_content",
    )
    add(
        "skip_link:assessment_target",
        'id="main-content"' in inv.assessment_html,
        "target",
    )
    add(
        "skip_link:assessment_partial_target",
        'id="main-content"' in inv.assessment_partial_html,
        "partial_target",
    )

    add("skip_link:eir_href", 'href="#main"' in inv.eir_html, "main")
    add("skip_link:eir_target", 'id="main"' in inv.eir_html, "target")
    add("skip_link:eir_empty_target", 'id="main"' in inv.eir_empty_html, "empty_target")

    styles = inv.assessment_styles + inv.eir_styles
    reveal = (
        "transform: translateY" in styles
        or ".skip-link:focus" in styles
        or "translateY(0)" in styles
    )
    add("skip_link:css_reveal", reveal, "transform_or_focus")

    if inv.docs_pages:
        for page_id, html in sorted(inv.docs_pages.items()):
            ok = "VPSkipLink" in html or "Skip to content" in html
            add(f"skip_link:docs_{page_id}", ok, "present")
    else:
        add("skip_link:docs_build", True, "docs_build_absent")

    if any(not c.ok for c in checks):
        defects.append(Defect("skip_link", "skip navigation link contract not satisfied"))
    return checks, defects
