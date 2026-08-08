"""Negative scenarios A–Z for Slice 14.13 (pass when defects absent)."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add, scan_hex
from verification.cross_surface_visual_consistency.contract import (
    FORBIDDEN_15_7_PATHS,
    LEGACY_AMBER_HEX,
)
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_scenarios(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    scenarios: tuple[tuple[str, str, bool], ...] = (
        ("A", "policy_loaded", bool(inv.policy)),
        ("B", "contract_loaded", bool(inv.consistency_contract)),
        ("C", "token_catalog_loaded", bool(inv.token_catalog)),
        ("D", "public_tokens_no_amber", not scan_hex(inv.public_tokens, LEGACY_AMBER_HEX)),
        ("E", "swagger_tokens_no_amber", not scan_hex(inv.swagger_tokens, LEGACY_AMBER_HEX)),
        ("F", "assessment_mark_present", "report-product-mark" in inv.assessment_renderer),
        ("G", "eir_mark_present", "report-product-mark" in inv.eir_renderer),
        ("H", "docs_teal_tokens", "--cs-teal" in inv.docs_theme_tokens),
        ("I", "swagger_teal_vars", "var(--cs-teal" in inv.swagger_css),
        ("J", "vscode_native_mapping", bool(inv.vscode_mapping)),
        ("K", "marketplace_mapping", bool(inv.marketplace_mapping)),
        ("L", "brand_masters", "codestrata-mark.svg" in inv.brand_masters),
        ("M", "assessment_renders", bool(inv.assessment_html)),
        ("N", "eir_renders", bool(inv.eir_html)),
        ("O", "slice_15_7_absent", not any((inv.monorepo / p).exists() for p in FORBIDDEN_15_7_PATHS)),
        ("P", "dist_or_buildable", inv.dist_exists),
        ("Q", "consumer_mappings", bool(inv.consumer_mappings)),
        ("R", "presentation_contract", bool(inv.presentation_contract)),
        ("S", "no_amber_assessment", not scan_hex(inv.assessment_styles, LEGACY_AMBER_HEX)),
        ("T", "no_amber_eir", not scan_hex(inv.eir_styles, LEGACY_AMBER_HEX)),
        ("U", "codestrata_naming", inv.policy.get("authoritative_product_name") == "CodeStrata"),
        ("V", "docs_community_scope", "srcExclude" in inv.docs_config),
        ("W", "adaptations_eight", len(inv.consistency_contract.get("adaptations") or []) >= 8),
        ("X", "matrix_rows", len(inv.consistency_contract.get("matrix", {}).get("rows") or []) >= 10),
        ("Y", "matrix_columns", len(inv.consistency_contract.get("matrix", {}).get("columns") or []) == 6),
        ("Z", "design_system_1_0", inv.policy.get("design_system_version") == "1.0"),
    )
    for letter, name, ok in scenarios:
        add(checks, f"scenario:{letter}:{name}", ok, name, "scenarios")
    return checks
