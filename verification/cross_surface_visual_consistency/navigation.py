"""Navigation consistency checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_navigation(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []

    add(
        checks,
        "navigation:assessment_toc_aria",
        'aria-label="Table of contents"' in inv.assessment_html
        or "Table of contents" in inv.assessment_renderer,
        "assessment_toc",
        "navigation",
    )
    add(
        checks,
        "navigation:eir_toc_aria",
        'aria-label="Table of contents"' in inv.eir_html
        or "Table of contents" in inv.eir_renderer,
        "eir_toc",
        "navigation",
    )
    add(
        checks,
        "navigation:docs_community_only",
        "platform/" not in inv.docs_config.lower()
        or "srcExclude" in inv.docs_config,
        "no_platform_nav",
        "navigation",
    )
    dist_index = inv.monorepo / "docs" / ".vitepress" / "dist" / "index.html"
    dist_html = dist_index.read_text(encoding="utf-8") if dist_index.is_file() else ""
    add(
        checks,
        "navigation:docs_skip_link",
        "VPSkipLink" in dist_html
        or "Skip to content" in dist_html
        or "skip" in inv.docs_config.lower(),
        "docs_skip",
        "navigation",
    )
    return checks
