"""Typography checks for Slice 14.11."""

from __future__ import annotations

import re

from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "typography"
_TOO_SMALL = re.compile(
    r"font-size:\s*(?:0\.(?:[0-5]\d*|6[^2-9]\d*)|10px|11px|12px)",
    re.IGNORECASE,
)


def check_typography(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    typo = inv.token_catalog.get("typography", {})
    add(
        "typography:catalog_body_size",
        typo.get("body_size_px") == 16,
        str(typo.get("body_size_px")),
    )
    add(
        "typography:catalog_body_line_height",
        typo.get("body_line_height") == 1.65,
        str(typo.get("body_line_height")),
    )

    for surface, styles in (("assessment", inv.assessment_styles), ("eir", inv.eir_styles)):
        add(
            f"typography:{surface}_body_relative",
            "font: 1rem/" in styles or "font-size: 1rem" in styles,
            "relative_body",
        )
        add(
            f"typography:{surface}_no_root_16px",
            not re.search(r"html\s*\{[^}]*font-size:\s*16px", styles, re.IGNORECASE | re.DOTALL),
            "no_fixed_root",
        )
        tiny = _TOO_SMALL.findall(styles)
        add(
            f"typography:{surface}_min_font_size",
            not tiny,
            "ok" if not tiny else f"{len(tiny)}_violations",
        )
        add(
            f"typography:{surface}_mono_token",
            "var(--cs-font-mono)" in styles,
            "mono_token",
        )

    docs_css = inv.docs_css
    docs_bridge = "design-system/tokens/tokens.css" in inv.docs_tokens_css
    add(
        "typography:docs_body_line_height",
        docs_bridge
        or "--cs-lh-body" in docs_css
        or "line-height: 1.65" in docs_css
        or "1.65" in docs_css,
        "lh_reference" if docs_bridge or "--cs-lh-body" in docs_css else "bridge_or_value",
    )

    if any(not c.ok for c in checks):
        defects.append(Defect("typography", "typography contract not satisfied on one or more surfaces"))
    return checks, defects
