"""HTML language attribute checks."""

from __future__ import annotations

from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "html_language"


def check_html_language(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    for surface, html in (("assessment", inv.assessment_html), ("eir", inv.eir_html)):
        add(
            f"html_language:{surface}_lang_en",
            '<html lang="en' in html.lower(),
            "en",
        )

    add(
        "html_language:docs_config",
        'lang: "en' in inv.docs_config or "lang: 'en" in inv.docs_config,
        "config",
    )

    if inv.docs_pages:
        for page_id, html in sorted(inv.docs_pages.items()):
            add(
                f"html_language:docs_{page_id}",
                'lang="en' in html.lower(),
                "en",
            )
    else:
        add("html_language:docs_pages_absent", True, "skipped")

    if any(not c.ok for c in checks):
        defects.append(Defect("html_language", "page language not declared"))
    return checks, defects
