"""Legacy branding scan for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add, scan_forbidden, scan_hex
from verification.cross_surface_visual_consistency.contract import (
    FORBIDDEN_ACTIVE_IDENTITY,
    LEGACY_AMBER_HEX,
)
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult, Defect


ACTIVE_PATHS = (
    "docs/.vitepress/theme/tokens.css",
    "docs/public/design-tokens/tokens.css",
    "platform/api/openapi/swagger/design-tokens/tokens.css",
    "platform/api/openapi/swagger/css/codestrata-swagger.css",
    "engine/src/codestrata/reporting/html_v2/styles.py",
    "platform/src/codestrata_platform/intelligence_reporting/presentation/static_html/styles.py",
    "vscode-plugin/media/codestrata-activity.svg",
)


def check_legacy_branding(
    inv: ConsistencyInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    for rel in ACTIVE_PATHS:
        text = (inv.monorepo / rel).read_text(encoding="utf-8") if (inv.monorepo / rel).is_file() else ""
        name = rel.split("/")[-1]
        amber = scan_hex(text, LEGACY_AMBER_HEX)
        add(
            checks,
            f"legacy_branding:{name}:no_amber",
            not amber,
            "clean" if not amber else "amber",
            "legacy_branding",
        )
        if amber:
            defects.append(Defect("legacy_branding", f"amber in {rel}"))

    combined = "".join(
        (inv.monorepo / rel).read_text(encoding="utf-8")
        for rel in ACTIVE_PATHS
        if (inv.monorepo / rel).is_file()
    )
    forbidden = scan_forbidden(combined, FORBIDDEN_ACTIVE_IDENTITY)
    add(
        checks,
        "legacy_branding:no_aimf_georgia",
        not forbidden,
        "clean" if not forbidden else ",".join(forbidden),
        "legacy_branding",
    )
    return checks, defects
