"""Documentation site responsive checks."""

from __future__ import annotations

from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "documentation_responsive"


def check_docs_responsive(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    custom = inv.docs_custom_css
    add(
        "documentation_responsive:footer_stack_720",
        "720px" in custom and "cs-footer" in custom,
        "footer_stack",
    )
    add(
        "documentation_responsive:table_overflow",
        ".VPDoc table" in inv.docs_components_css
        and "overflow-x: auto" in inv.docs_components_css,
        "table",
    )
    add(
        "documentation_responsive:home_touch_44",
        "min-height: 44px" in custom and "cs-docs-home" in custom,
        "44px",
    )
    add(
        "documentation_responsive:tokens_wrap",
        "overflow-wrap: anywhere" in inv.docs_tokens_css,
        "anywhere",
    )
    add(
        "documentation_responsive:config_lang",
        'lang: "en' in inv.docs_config or "lang: 'en" in inv.docs_config,
        "en",
    )

    if inv.docs_pages:
        for page_id, html in sorted(inv.docs_pages.items()):
            add(
                f"documentation_responsive:skip_{page_id}",
                "Skip to content" in html or "VPSkipLink" in html,
                "skip",
            )
            add(
                f"documentation_responsive:lang_{page_id}",
                'lang="en' in html.lower(),
                "lang",
            )
    else:
        add("documentation_responsive:pages_absent", True, "docs_build_absent")

    if any(not c.ok for c in checks):
        defects.append(Defect("documentation_responsive", "documentation responsive contract not met"))
    return checks, defects
