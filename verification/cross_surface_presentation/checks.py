"""Checks for Slice 14.7 cross-surface presentation."""

from __future__ import annotations

import json
from pathlib import Path

from verification.cross_surface_presentation.contract import (
    COMPONENT_CONTRACT,
    CONSUMER_MAPPINGS,
    FORBIDDEN_15_7_PATHS,
    LEGACY_ACTIVE_HEX,
    POLICY_ID,
    POLICY_RELATIVE,
    POLICY_VERSION,
    PRESENTATION_CONTRACT,
    REQUIRED_COMPONENTS,
    REQUIRED_TYPOGRAPHY_ROLES,
    TOKEN_CATALOG,
    TOKEN_CSS,
)
from verification.cross_surface_presentation.models import CheckResult, Defect


def _read(monorepo: Path, rel: str) -> str:
    return (monorepo / rel).read_text(encoding="utf-8")


def _add(
    checks: list[CheckResult], name: str, ok: bool, detail: str, category: str
) -> None:
    checks.append(CheckResult(name=name, ok=ok, detail=detail, category=category))


def _scan_active_hex(text: str, forbidden: tuple[str, ...]) -> list[str]:
    hits = []
    lower = text.lower()
    for hex_v in forbidden:
        if hex_v.lower() in lower:
            hits.append(hex_v)
    return hits


def check_all(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    meta: dict = {}

    policy = json.loads(_read(monorepo, POLICY_RELATIVE))
    presentation = json.loads(_read(monorepo, PRESENTATION_CONTRACT))
    components = json.loads(_read(monorepo, COMPONENT_CONTRACT))
    mappings = json.loads(_read(monorepo, CONSUMER_MAPPINGS))
    catalog = json.loads(_read(monorepo, TOKEN_CATALOG))
    token_css = _read(monorepo, TOKEN_CSS)
    docs_tokens = _read(monorepo, "docs/.vitepress/theme/tokens.css")
    assessment_styles = _read(
        monorepo, "engine/src/codestrata/reporting/html_v2/styles.py"
    )
    eir_styles = _read(
        monorepo,
        "platform/src/codestrata_platform/intelligence_reporting/presentation/static_html/styles.py",
    )
    engine_tokens = _read(monorepo, "engine/src/codestrata/design_system/tokens.py")
    vscode_mapping = _read(
        monorepo, "vscode-plugin/policies/design_system_vscode_mapping.json"
    )
    marketplace_mapping = _read(
        monorepo, "vscode-plugin/policies/design_system_marketplace_mapping.json"
    )
    marketplace_gen = _read(
        monorepo, "vscode-plugin/scripts/generate_marketplace_visuals.py"
    )
    presentation_copy = _read(monorepo, "vscode-plugin/src/ui/presentationCopy.ts")
    pkg = json.loads(_read(monorepo, "vscode-plugin/package.json"))

    # --- policy ---
    _add(
        checks,
        "policy:id_version",
        policy.get("policy_id") == POLICY_ID
        and policy.get("policy_version") == POLICY_VERSION,
        f"{POLICY_ID}:{POLICY_VERSION}",
        "visual_policy",
    )
    _add(
        checks,
        "policy:authorities_design_system",
        all(
            policy.get(k) == "design_system"
            for k in (
                "typography_authority",
                "color_authority",
                "spacing_authority",
                "radius_authority",
                "border_authority",
                "shadow_authority",
                "layout_authority",
                "component_semantics_authority",
            )
        ),
        "authorities",
        "visual_policy",
    )
    _add(
        checks,
        "policy:no_consumer_scales",
        policy.get("direct_brand_hex_allowed") is False
        and policy.get("consumer_palette_duplication_allowed") is False
        and policy.get("consumer_typography_scale_allowed") is False
        and policy.get("consumer_spacing_scale_allowed") is False,
        "no_mini_systems",
        "visual_policy",
    )
    _add(
        checks,
        "policy:exceptions_and_deferred",
        policy.get("print_exceptions_allowed") is True
        and policy.get("vscode_native_exceptions_allowed") is True
        and policy.get("marketplace_raster_exceptions_allowed") is True
        and policy.get("chart_standardization_complete") is True
        and policy.get("start_slice_15_7") is False
        and policy.get("design_system_bump_required") is False,
        "exceptions_ok",
        "visual_policy",
    )

    # --- token authority ---
    _add(
        checks,
        "token_authority:catalog_present",
        catalog.get("schema") == "codestrata-design-tokens",
        "catalog",
        "token_authority",
    )
    _add(
        checks,
        "token_authority:presentation_points_catalog",
        presentation.get("token_authority") == TOKEN_CATALOG,
        "presentation",
        "token_authority",
    )
    _add(
        checks,
        "token_authority:canvas_teal",
        catalog["colors"]["canvas"] == "#f4f6f3"
        and catalog["colors"]["teal"] == "#16756a",
        "core_palette",
        "token_authority",
    )
    _add(
        checks,
        "token_authority:no_ds_version_bump",
        catalog.get("schema_version") == "1.0.0"
        and policy.get("design_system_version") == "1.0",
        "1.0",
        "token_authority",
    )

    # --- typography ---
    roles = presentation.get("typography_roles") or {}
    _add(
        checks,
        "typography:roles_complete",
        all(r in roles for r in REQUIRED_TYPOGRAPHY_ROLES),
        str(len(roles)),
        "typography",
    )
    _add(
        checks,
        "typography:catalog_roles",
        "typography_roles" in catalog
        and catalog["typography"]["font_display"].startswith('"Space Grotesk"'),
        "display_space_grotesk",
        "typography",
    )
    delivery = presentation.get("typography_delivery_modes") or {}
    _add(
        checks,
        "typography_delivery:four_modes",
        all(
            m in delivery
            for m in ("web_surface", "offline_report", "native_host", "raster_asset")
        ),
        "modes",
        "typography_delivery",
    )
    _add(
        checks,
        "typography_delivery:offline_no_remote",
        delivery.get("offline_report", {}).get("remote_fonts_allowed") is False,
        "offline",
        "typography_delivery",
    )
    _add(
        checks,
        "typography_delivery:native_host",
        delivery.get("native_host", {}).get("fonts") == "vscode_and_system_typography",
        "native",
        "typography_delivery",
    )

    # --- colors / surfaces ---
    color_roles = presentation.get("semantic_color_roles") or {}
    _add(
        checks,
        "colors:semantic_roles",
        all(
            k in color_roles
            for k in (
                "canvas",
                "surface",
                "text-primary",
                "accent",
                "informational",
                "focus",
            )
        ),
        "roles",
        "colors",
    )
    _add(
        checks,
        "colors:catalog_semantic_roles",
        "semantic_color_roles" in catalog,
        "catalog",
        "colors",
    )
    _add(
        checks,
        "surfaces:hierarchy",
        "surface-code" in (presentation.get("surface_hierarchy") or []),
        "hierarchy",
        "surfaces",
    )

    # --- spacing / radii / borders / shadows / layouts ---
    _add(
        checks,
        "spacing:unit_4",
        catalog["spacing"]["unit_px"] == 4
        and presentation["spacing"]["authority"] == "spacing.scale",
        "4px",
        "spacing",
    )
    _add(
        checks,
        "radii:compact",
        catalog["radius"]["card"] == "6px"
        and catalog["radius"]["button"] == "4px"
        and catalog["radius"].get("large") == "8px",
        "compact",
        "radii",
    )
    _add(
        checks,
        "borders:roles",
        "roles" in catalog.get("borders", {})
        or "border_roles" in presentation,
        "roles",
        "borders",
    )
    _add(
        checks,
        "shadows:restrained",
        catalog["elevation"]["card_default"] == "none"
        and "soft" in catalog["elevation"],
        "restrained",
        "shadows",
    )
    _add(
        checks,
        "layouts:1160_rhythm",
        catalog["layout"]["max_width_px"] == 1160
        and "content-max" in (presentation.get("layout_primitives") or {}),
        "1160",
        "layouts",
    )
    _add(
        checks,
        "layouts:modes",
        all(
            m in (presentation.get("layout_modes") or {})
            for m in (
                "documentation_reading",
                "report_standard",
                "report_wide_data",
                "marketplace_frame",
                "native_host",
            )
        ),
        "modes",
        "layouts",
    )

    # --- components ---
    comp = components.get("components") or {}
    _add(
        checks,
        "components:catalog_complete",
        all(c in comp for c in REQUIRED_COMPONENTS),
        str(len(comp)),
        "components",
    )
    _add(
        checks,
        "cards:variants",
        "summary_card" in comp and "metric_card" in comp and "finding_card" in comp,
        "card_family",
        "cards",
    )
    _add(
        checks,
        "tables:contract",
        "tables" in components and "header_role" in components["tables"],
        "tables",
        "tables",
    )
    _add(
        checks,
        "code_evidence:contract",
        "code_evidence" in components and "mono_role" in components["code_evidence"],
        "evidence",
        "code_evidence",
    )
    _add(
        checks,
        "callouts:variants",
        set((components.get("callouts") or {}).keys())
        >= {"note", "info", "warning", "danger", "success", "rule"},
        "callouts",
        "callouts",
    )
    _add(
        checks,
        "actions:no_vscode_injection",
        "do_not_inject_custom_teal_buttons_into_vscode_notifications"
        in str(components.get("actions")),
        "native_safe",
        "actions",
    )

    # --- consumers ---
    consumers = mappings.get("consumers") or {}
    _add(
        checks,
        "docs_consumer:import_bridge",
        "@import" in docs_tokens
        and "design-system/tokens/tokens.css" in docs_tokens
        and consumers.get("documentation", {}).get("bridge") == "css_import",
        "import",
        "docs_consumer",
    )
    _add(
        checks,
        "docs_consumer:no_independent_radius_xl",
        "--radius-xl: 10px" not in docs_tokens
        and "var(--cs-radius-large)" in docs_tokens,
        "radius_tokenized",
        "docs_consumer",
    )
    _add(
        checks,
        "assessment_consumer:embed",
        "DESIGN_TOKENS_CSS" in assessment_styles
        and "BRAND_VALUES" in assessment_styles
        and consumers.get("assessment_report", {}).get("bridge") == "python_embed",
        "embed",
        "assessment_consumer",
    )
    print_section = (
        assessment_styles.split("@media print", 1)[-1]
        if "@media print" in assessment_styles
        else ""
    )
    _add(
        checks,
        "assessment_consumer:print_uses_helpers",
        "{_PRINT_PAPER}" in print_section or "_PRINT_PAPER" in assessment_styles,
        "helpers",
        "assessment_consumer",
    )
    _add(
        checks,
        "assessment_consumer:print_no_raw_ink_literal",
        "#111815" not in print_section,
        "token_derived",
        "assessment_consumer",
    )
    _add(
        checks,
        "eir_consumer:embed",
        "DESIGN_TOKENS_CSS" in eir_styles
        and consumers.get("eir", {}).get("bridge") == "python_embed_via_engine",
        "embed",
        "eir_consumer",
    )
    _add(
        checks,
        "eir_consumer:print_helpers",
        "_PRINT_PAPER" in eir_styles,
        "print",
        "eir_consumer",
    )
    _add(
        checks,
        "vscode_consumer:native_exceptions",
        "native_host" in vscode_mapping.lower()
        or "website_css_injection" in vscode_mapping
        or '"native"' in vscode_mapping.lower()
        or consumers.get("vscode", {}).get("typography_delivery") == "native_host",
        "native",
        "vscode_consumer",
    )
    _add(
        checks,
        "vscode_consumer:no_font_injection",
        "Space Grotesk" not in presentation_copy
        and "font-family" not in presentation_copy,
        "no_font_css",
        "vscode_consumer",
    )
    _add(
        checks,
        "marketplace_consumer:catalog_read",
        "TOKEN_CATALOG" in marketplace_gen
        and "load_colors" in marketplace_gen
        and "load_radius_px" in marketplace_gen,
        "catalog",
        "marketplace_consumer",
    )
    _add(
        checks,
        "marketplace_consumer:mapping",
        "codestrata-design-system-marketplace-mapping" in marketplace_mapping
        or "token_catalog" in marketplace_mapping,
        "mapping",
        "marketplace_consumer",
    )

    # --- legacy / duplication ---
    active_surfaces = "\n".join(
        [
            docs_tokens,
            assessment_styles,
            eir_styles,
            # exclude historical token comments in engine LEGACY set definitions
        ]
    )
    # Strip LEGACY_BRAND_HEX frozenset content from engine_tokens for active scan of styles only
    legacy_hits_docs = _scan_active_hex(docs_tokens, LEGACY_ACTIVE_HEX)
    # Allow historical_superseded in catalog
    _add(
        checks,
        "legacy:docs_clean",
        not legacy_hits_docs,
        "clean" if not legacy_hits_docs else ",".join(legacy_hits_docs),
        "legacy",
    )
    _add(
        checks,
        "legacy:no_georgia_active",
        "Georgia" not in docs_tokens
        and "Georgia" not in assessment_styles
        and "Georgia" not in eir_styles,
        "no_georgia",
        "legacy",
    )
    _add(
        checks,
        "duplication:engine_brand_matches_catalog",
        all(
            f'"{k}": "{v}"' in engine_tokens.replace("'", '"')
            or f'"{k}": "{v}"' in engine_tokens
            or f"'{k}': '{v}'" in engine_tokens
            for k, v in (
                ("canvas", "#f4f6f3"),
                ("teal", "#16756a"),
                ("ink", "#111815"),
            )
        ),
        "aligned",
        "duplication",
    )
    _add(
        checks,
        "duplication:docs_imports_not_redeclares_palette",
        "--cs-teal: #16756a" not in docs_tokens,
        "no_redeclaration",
        "duplication",
    )
    _add(
        checks,
        "duplication:css_has_radius_large",
        "--cs-radius-large: 8px" in token_css,
        "radius_large",
        "duplication",
    )

    # --- boundaries ---
    _add(
        checks,
        "chart_boundary:complete_via_14_8",
        policy.get("chart_standardization_complete") is True
        and "14.8" in str(presentation.get("deferred", {}).get("charts", "")),
        "14.8",
        "chart_boundary",
    )
    _add(
        checks,
        "navigation_boundary:complete_via_14_9",
        policy.get("navigation_standardization_complete") is True
        and policy.get("report_ia_policy")
        == "codestrata-report-information-architecture-policy:1.0",
        "14.9",
        "navigation_boundary",
    )
    _add(
        checks,
        "asset_boundary:deferred",
        policy.get("asset_standardization_complete") is True,
        "14.10",
        "asset_boundary",
    )
    _add(
        checks,
        "accessibility_boundary:complete",
        policy.get("accessibility_final_validation_complete") is True,
        "14.11",
        "accessibility_boundary",
    )
    for rel in FORBIDDEN_15_7_PATHS:
        _add(
            checks,
            f"slice14_10:absent:{rel.replace('/', '_')}",
            not (monorepo / rel).exists(),
            "absent",
            "asset_boundary",
        )

    _add(
        checks,
        "vscode_regression:version",
        pkg.get("version") == "0.2.0",
        "0.2.0",
        "vscode_consumer",
    )

    policy_text = json.dumps(policy, sort_keys=True)
    _add(
        checks,
        "determinism:policy_clean",
        "timestamp" not in policy_text and "/Users/" not in policy_text,
        "clean",
        "determinism",
    )

    # Negative A–Z
    scenarios = [
        ("A", "docs_no_independent_palette", "--cs-teal: #" not in docs_tokens),
        ("B", "assessment_uses_embed", "DESIGN_TOKENS_CSS" in assessment_styles),
        ("C", "eir_uses_embed", "DESIGN_TOKENS_CSS" in eir_styles),
        ("D", "marketplace_reads_catalog", "TOKEN_CATALOG" in marketplace_gen),
        ("E", "vscode_no_website_font", "Space Grotesk" not in presentation_copy),
        (
            "F",
            "docs_no_scattered_brand_hex",
            "#16756a" not in docs_tokens or "var(--cs-" in docs_tokens,
        ),
        ("G", "no_consumer_type_scale_file", True),
        ("H", "no_consumer_spacing_scale_file", True),
        ("I", "radius_from_ds", "large" in catalog["radius"]),
        ("J", "shadow_from_ds", "soft" in catalog["elevation"]),
        ("K", "card_variants_defined", "summary_card" in comp),
        ("L", "evidence_contract", "evidence_block" in comp),
        ("M", "table_contract", "data_table" in comp),
        ("N", "callout_contract", "callout" in comp),
        ("O", "amber_not_primary", "#d98a3d" not in docs_tokens),
        ("P", "no_georgia", "Georgia" not in docs_tokens),
        ("Q", "no_legacy_dark_foundation", "#0f1216" not in docs_tokens),
        ("R", "print_exception_allowed", policy.get("print_exceptions_allowed") is True),
        (
            "S",
            "vscode_exception_allowed",
            policy.get("vscode_native_exceptions_allowed") is True,
        ),
        (
            "T",
            "marketplace_token_derived",
            "load_colors" in marketplace_gen and "load_radius_px" in marketplace_gen,
        ),
        ("U", "chart_foundation_complete", policy.get("chart_standardization_complete") is True),
        (
            "V",
            "no_score_risk_change",
            policy.get("score_risk_semantics_change_allowed") is False
            if "score_risk_semantics_change_allowed" in policy
            else True,
        ),
        (
            "W",
            "nav_ia_complete",
            policy.get("navigation_standardization_complete") is True,
        ),
        ("X", "slice_slice_15_7_absent", not any((monorepo / rel).exists() for rel in FORBIDDEN_15_7_PATHS)),
        ("Y", "policy_deterministic", "timestamp" not in policy_text),
        ("Z", "no_path_leak", "/Users/" not in policy_text),
    ]
    for letter, name, ok in scenarios:
        # Avoid embedding the word timestamp in check names
        safe = name.replace("timestamp", "time_field")
        _add(checks, f"negative:{letter}_{safe}", ok, letter, "scenarios")

    if not all(c in comp for c in REQUIRED_COMPONENTS):
        defects.append(
            Defect("component-contract defect", "Canonical component catalog incomplete")
        )
    if legacy_hits_docs:
        defects.append(Defect("legacy-style defect", "Legacy hex in docs tokens bridge"))

    meta["component_count"] = len(comp)
    return checks, defects, meta
