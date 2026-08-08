"""Dark theme contrast token checks."""

from __future__ import annotations

from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "dark_theme"


def check_dark_theme(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    tokens = inv.engine_tokens

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    for token in ("--cs-teal-light", "--cs-rust-light", "--cs-blue-light"):
        add(f"dark_theme:engine_{token.strip('-')}", token in tokens, "present")

    add(
        "dark_theme:engine_risk_remap",
        "var(--cs-rust-light)" in tokens and "--cs-risk-critical" in tokens,
        "remapped",
    )
    add(
        "dark_theme:token_css_tints",
        "teal-light" in inv.token_css or "--cs-teal-light" in inv.token_css,
        "css",
    )
    add(
        "dark_theme:catalog_dark_colors",
        bool(inv.token_catalog.get("dark_theme_colors"))
        or "teal_light" in inv.token_catalog.get("colors", {}),
        "catalog",
    )
    add(
        "dark_theme:assessment_embeds_tints",
        "#35b3a4" in inv.assessment_html or "--cs-teal-light" in inv.assessment_html,
        "inlined",
    )
    add(
        "dark_theme:docs_bridge",
        'data-theme="dark"' in inv.docs_tokens_css
        or "html.dark" in inv.docs_tokens_css
        or ".dark" in inv.docs_tokens_css,
        "bridge",
    )

    if any(not c.ok for c in checks):
        defects.append(Defect("dark_theme", "dark theme contrast tokens incomplete"))
    return checks, defects
