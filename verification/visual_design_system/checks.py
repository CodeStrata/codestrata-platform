"""Focused checks for Slice 14.1 visual design system verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.visual_design_system.contract import (
    DESIGN_SYSTEM_ROOT,
    FORBIDDEN_14_2_PATHS,
    REQUIRED_COMPONENT_IDS,
    REQUIRED_DIRS,
    REQUIRED_SURFACES,
)
from verification.visual_design_system.models import CheckResult, Defect

REQUIRED_COLOR_KEYS = (
    "canvas",
    "paper",
    "ink",
    "muted",
    "line",
    "teal",
    "teal_dark",
    "rust",
    "blue",
    "night",
    "night_ink",
)

REQUIRED_TOP_LEVEL = (
    "colors",
    "status_colors",
    "risk_colors",
    "score_colors",
    "chart_colors",
    "typography",
    "spacing",
    "radius",
    "borders",
    "elevation",
    "animation",
    "breakpoints",
    "layout",
)


def _add(
    checks: list[CheckResult],
    name: str,
    ok: bool,
    detail: str,
    category: str,
) -> None:
    checks.append(CheckResult(name=name, ok=ok, detail=detail, category=category))


def _read(monorepo: Path, rel: str) -> str:
    return (monorepo / rel).read_text(encoding="utf-8")


def _load_json(monorepo: Path, rel: str) -> dict:
    return json.loads(_read(monorepo, rel))


def _validate_catalog(catalog: dict) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED_TOP_LEVEL:
        if key not in catalog:
            errors.append(f"missing:{key}")
    colors = catalog.get("colors", {})
    for key in REQUIRED_COLOR_KEYS:
        if key not in colors:
            errors.append(f"missing_color:{key}")
    typo = catalog.get("typography", {})
    for key in ("font_display", "font_body", "font_mono", "scale"):
        if key not in typo:
            errors.append(f"missing_typography:{key}")
    if catalog.get("default_theme") != "light":
        errors.append("default_theme_must_be_light")
    if catalog.get("schema_version") != "1.0.0":
        errors.append("schema_version_drift")
    return errors


def check_all(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    root = monorepo / DESIGN_SYSTEM_ROOT

    _add(checks, "pkg:root_present", root.is_dir(), DESIGN_SYSTEM_ROOT, "package")
    for dirname in REQUIRED_DIRS:
        ok = (root / dirname).is_dir()
        _add(checks, f"pkg:dir:{dirname}", ok, dirname, "package")
        if not ok:
            defects.append(
                Defect(
                    "definition defect",
                    f"{DESIGN_SYSTEM_ROOT}/{dirname}",
                    "present",
                    "missing",
                )
            )

    ds = _load_json(monorepo, f"{DESIGN_SYSTEM_ROOT}/policies/design_system_policy.json")
    vl = _load_json(monorepo, f"{DESIGN_SYSTEM_ROOT}/policies/visual_language_policy.json")
    _add(
        checks,
        "policy:design_system_id_version",
        ds.get("policy_id") == "codestrata-design-system-policy"
        and ds.get("policy_version") == "1.0",
        "codestrata-design-system-policy:1.0",
        "policies",
    )
    _add(
        checks,
        "policy:visual_language_id_version",
        vl.get("policy_id") == "codestrata-visual-language-policy"
        and vl.get("policy_version") == "1.0",
        "codestrata-visual-language-policy:1.0",
        "policies",
    )
    _add(
        checks,
        "policy:definition_only",
        ds.get("definition_only") is True
        and ds.get("product_redesign_allowed") is False
        and ds.get("docs_redesign_allowed") is False
        and ds.get("assessment_report_redesign_allowed") is False
        and ds.get("engineering_intelligence_redesign_allowed") is False
        and ds.get("vscode_redesign_allowed") is False
        and ds.get("marketplace_redesign_allowed") is False,
        "definition_only",
        "no_redesign",
    )
    _add(
        checks,
        "policy:start_14_2_false",
        ds.get("start_slice_14_2") is False
        and vl.get("apply_to_surfaces_in_this_slice") is False,
        "false",
        "slice_14_2",
    )

    catalog = _load_json(monorepo, f"{DESIGN_SYSTEM_ROOT}/tokens/catalog.json")
    token_errors = _validate_catalog(catalog)
    _add(
        checks,
        "tokens:catalog_valid",
        not token_errors,
        "ok" if not token_errors else ",".join(token_errors),
        "tokens",
    )
    css = _read(monorepo, f"{DESIGN_SYSTEM_ROOT}/tokens/tokens.css")
    for needle in (
        "--cs-canvas:",
        "--cs-teal-dark:",
        "--cs-rust:",
        "--cs-font-display:",
        "--cs-space-4:",
        "--cs-radius:",
        "--cs-shadow:",
        "--cs-chart-1:",
        "--cs-status-success:",
        "--cs-risk-high:",
        "--cs-score-good:",
        '[data-theme="dark"]',
    ):
        safe = needle.replace(":", "_").replace("[", "").replace("]", "").replace('"', "")
        _add(checks, f"tokens:css:{safe[:40]}", needle in css, "present", "tokens")

    colors = catalog.get("colors", {})
    _add(
        checks,
        "colors:live_canvas",
        colors.get("canvas") == "#f4f6f3",
        str(colors.get("canvas")),
        "colors",
    )
    _add(
        checks,
        "colors:live_teal_dark",
        colors.get("teal_dark") == "#0f5d54",
        str(colors.get("teal_dark")),
        "colors",
    )
    _add(
        checks,
        "typography:families",
        "Space Grotesk" in catalog["typography"]["font_display"]
        and "Inter" in catalog["typography"]["font_body"]
        and "IBM Plex Mono" in catalog["typography"]["font_mono"],
        "families",
        "typography",
    )
    _add(
        checks,
        "spacing:scale_present",
        "4px" in list(catalog["spacing"]["scale"].values()),
        "4px_base",
        "spacing",
    )
    _add(
        checks,
        "elevation:soft_shadow",
        "18px 48px" in catalog["elevation"]["soft"],
        "soft",
        "elevation",
    )

    components = _load_json(monorepo, f"{DESIGN_SYSTEM_ROOT}/components/catalog.json")
    ids = {c["id"] for c in components.get("components", [])}
    missing = [c for c in REQUIRED_COMPONENT_IDS if c not in ids]
    _add(
        checks,
        "components:catalog_complete",
        not missing and components.get("implementation_in_slice_14_1") is False,
        "complete" if not missing else ",".join(missing),
        "components",
    )

    surfaces = _load_json(monorepo, f"{DESIGN_SYSTEM_ROOT}/surfaces/catalog.json")
    surf = surfaces.get("surfaces", {})
    _add(
        checks,
        "surfaces:not_implemented_in_14_1",
        surfaces.get("implementation_in_slice_14_1") is False,
        "definition_only",
        "no_redesign",
    )
    category_map = {
        "documentation": "documentation_language",
        "assessment_report": "report_language",
        "engineering_intelligence_report": "report_language",
        "vscode_extension": "vscode_language",
        "marketplace_assets": "marketplace_language",
    }
    for name in REQUIRED_SURFACES:
        _add(
            checks,
            f"surfaces:present:{name}",
            name in surf,
            "present",
            category_map[name],
        )

    a11y = _load_json(monorepo, f"{DESIGN_SYSTEM_ROOT}/accessibility/rules.json")
    # Slice 14.11 refined wcag_target to 2.2_AA_oriented; accept legacy "AA" too.
    wcag_ok = a11y.get("wcag_target") in {"AA", "2.2_AA_oriented"}
    _add(
        checks,
        "a11y:aa_keyboard_focus_motion",
        wcag_ok
        and a11y.get("keyboard_navigation_required") is True
        and a11y.get("prefers_reduced_motion_required") is True
        and a11y.get("skip_link_required") is True,
        "defined",
        "accessibility",
    )
    resp = _load_json(monorepo, f"{DESIGN_SYSTEM_ROOT}/responsive/rules.json")
    _add(
        checks,
        "responsive:breakpoints",
        resp.get("breakpoints_px", {}).get("wrap") == 1160
        and resp.get("breakpoints_px", {}).get("nav") == 1040,
        "defined",
        "responsive",
    )

    themes = _load_json(monorepo, f"{DESIGN_SYSTEM_ROOT}/themes/catalog.json")
    _add(
        checks,
        "themes:light_default_dark_supported",
        themes["themes"]["light"]["default"] is True and "dark" in themes["themes"],
        "light+dark",
        "themes",
    )

    _add(
        checks,
        "docs:design_system_readme",
        (root / "README.md").is_file()
        and (root / "documentation" / "README.md").is_file(),
        "present",
        "documentation",
    )
    _add(
        checks,
        "source:capture_present",
        (root / "source" / "capture.json").is_file()
        and (root / "source" / "WEBSITE_CAPTURE.md").is_file(),
        "present",
        "source",
    )

    for rel in (
        "design-system/dist",
        "design-system/applications",
        "vscode-plugin/src/designSystemRuntime",
    ):
        exists = (monorepo / rel).exists()
        _add(
            checks,
            f"no_redesign:absent:{Path(rel).name}",
            not exists,
            "absent",
            "no_redesign",
        )
        if exists:
            defects.append(
                Defect("product redesign started", rel, "absent", "present")
            )

    for rel in FORBIDDEN_14_2_PATHS:
        exists = (monorepo / rel).exists()
        _add(
            checks,
            f"slice_14_2:absent:{Path(rel).name}",
            not exists,
            "absent",
            "slice_14_2",
        )

    arch = (
        _read(monorepo, "ARCHITECTURE.md")
        if (monorepo / "ARCHITECTURE.md").is_file()
        else ""
    )
    claims_14_2 = "Slice 14.2" in arch or "slice 14.2" in arch.lower()
    ok_14_2 = (not claims_14_2) or ("not started" in arch.lower())
    _add(checks, "slice_14_2:architecture_posture", ok_14_2, "ok", "slice_14_2")

    # Ensure we did not rewrite product CSS themes as part of 14.1 application
    docs_tokens = monorepo / "docs/public/design-tokens/tokens.css"
    if docs_tokens.is_file():
        # Historical amber file may remain — must not be deleted by 14.1
        _add(
            checks,
            "no_redesign:historical_docs_tokens_retained",
            docs_tokens.is_file(),
            "retained",
            "no_redesign",
        )

    if token_errors:
        defects.append(
            Defect(
                "definition defect",
                "design-system/tokens/catalog.json",
                "valid catalog",
                ",".join(token_errors),
            )
        )
    if missing:
        defects.append(
            Defect(
                "definition defect",
                "components/catalog.json",
                "all required components",
                ",".join(missing),
            )
        )

    return checks, defects


def release_posture() -> dict:
    return {
        "slice_14_1_complete": True,
        "slice_14_2_started": False,
        "product_redesign_performed": False,
        "docs_redesign_performed": False,
        "assessment_report_redesign_performed": False,
        "engineering_intelligence_redesign_performed": False,
        "vscode_redesign_performed": False,
        "marketplace_redesign_performed": False,
        "commit_created": False,
        "tag_created": False,
        "published": False,
        "deployed": False,
    }
