"""Heading hierarchy checks."""

from __future__ import annotations

from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "heading"


def _h1_count(html: str) -> int:
    return html.lower().count("<h1")


def check_headings(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    for surface, html in (
        ("assessment", inv.assessment_html),
        ("assessment_partial", inv.assessment_partial_html),
        ("eir", inv.eir_html),
        ("eir_empty", inv.eir_empty_html),
    ):
        count = _h1_count(html)
        add(f"heading:{surface}_single_h1", count == 1, str(count))

    if inv.docs_pages:
        for page_id, html in sorted(inv.docs_pages.items()):
            count = _h1_count(html)
            add(f"heading:docs_{page_id}_single_h1", count == 1, str(count))
    else:
        add("heading:docs_pages_absent", True, "skipped")

    add(
        "heading:assessment_eyebrow_hidden",
        'class="section-eyebrow" aria-hidden="true"' in inv.assessment_html
        or "section-eyebrow" in inv.assessment_html and 'aria-hidden="true"' in inv.assessment_html,
        "decorative_hidden",
    )

    if any(not c.ok for c in checks):
        defects.append(Defect("heading", "heading hierarchy requirements not met"))
    return checks, defects
