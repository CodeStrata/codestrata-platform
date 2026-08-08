"""Landmark region checks."""

from __future__ import annotations

import re

from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "landmark"


def check_landmarks(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    assessment = inv.assessment_html
    banner = assessment.count('role="banner"')
    add("landmark:assessment_banner", banner == 1, str(banner))
    main_count = len(re.findall(r"<main\b", assessment, flags=re.I))
    add("landmark:assessment_main", main_count == 1, str(main_count))
    main_end = assessment.lower().rfind("</main>")
    footer_pos = assessment.lower().find("<footer")
    add(
        "landmark:assessment_footer_after_main",
        main_end >= 0 and footer_pos > main_end,
        "ordered",
    )

    eir = inv.eir_html
    add("landmark:eir_banner", eir.count('role="banner"') == 1, "one")
    add("landmark:eir_main", len(re.findall(r"<main\b", eir, flags=re.I)) == 1, "one")
    add(
        "landmark:eir_cover_section",
        '<section class="cover"' in eir,
        "section",
    )
    add("landmark:eir_footer", "<footer" in eir.lower(), "present")

    for surface, html in (("assessment", inv.assessment_html), ("eir", inv.eir_html)):
        add(
            f"landmark:{surface}_toc_labelled",
            'aria-label="Table of contents"' in html,
            "labelled",
        )

    add(
        "landmark:docs_footer_semantic",
        'role="contentinfo"' in inv.docs_footer or "<footer" in inv.docs_footer.lower(),
        "contentinfo",
    )

    if any(not check.ok for check in checks):
        defects.append(Defect("landmark", "landmark regions incomplete or duplicated"))
    return checks, defects
