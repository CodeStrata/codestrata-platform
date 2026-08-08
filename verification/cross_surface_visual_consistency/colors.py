"""Color consistency checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add, scan_hex
from verification.cross_surface_visual_consistency.contract import LEGACY_AMBER_HEX
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_colors(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    catalog = inv.token_catalog.get("colors") or {}
    teal = catalog.get("teal", "")
    rust = catalog.get("rust", "")

    surfaces = {
        "docs_theme": inv.docs_theme_tokens,
        "public_tokens": inv.public_tokens,
        "swagger_tokens": inv.swagger_tokens,
        "swagger_css": inv.swagger_css,
        "assessment_styles": inv.assessment_styles,
        "eir_styles": inv.eir_styles,
        "vscode_activity": inv.vscode_activity_svg,
        "dist_tokens": inv.dist_tokens,
    }

    for name, text in surfaces.items():
        if not text and name == "dist_tokens":
            continue
        add(
            checks,
            f"colors:{name}:no_amber",
            not scan_hex(text, LEGACY_AMBER_HEX),
            "clean" if not scan_hex(text, LEGACY_AMBER_HEX) else "amber_found",
            "colors",
        )

    add(
        checks,
        "colors:catalog_teal_rust",
        teal == "#16756a" and rust,
        f"teal={teal}",
        "colors",
    )
    add(
        checks,
        "colors:public_teal_tokens",
        "--cs-teal" in inv.public_tokens,
        "teal_tokens",
        "colors",
    )
    add(
        checks,
        "colors:swagger_teal_vars",
        "var(--cs-teal" in inv.swagger_css or "--cs-teal" in inv.swagger_css,
        "swagger_teal",
        "colors",
    )
    add(
        checks,
        "colors:marketplace_forbidden_list",
        LEGACY_AMBER_HEX in inv.marketplace_mapping,
        "forbidden_in_mapping",
        "colors",
    )
    return checks
