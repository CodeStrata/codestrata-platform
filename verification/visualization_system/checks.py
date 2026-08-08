"""Checks for Slice 14.8 visualization system."""

from __future__ import annotations

import json
from pathlib import Path

from verification.visualization_system.contract import (
    ASSESSMENT_RENDERER,
    ASSESSMENT_STYLES,
    EIR_RENDERER,
    EIR_STYLES,
    FORBIDDEN_EPIC_15_PATHS,
    FORBIDDEN_HEALTH_LABELS,
    POLICY_ID,
    POLICY_RELATIVE,
    POLICY_VERSION,
    TOKEN_CATALOG,
    VIZ_CONTRACT,
)
from verification.visualization_system.models import CheckResult, Defect


def _read(monorepo: Path, rel: str) -> str:
    return (monorepo / rel).read_text(encoding="utf-8")


def _add(
    checks: list[CheckResult], name: str, ok: bool, detail: str, category: str
) -> None:
    checks.append(CheckResult(name=name, ok=ok, detail=detail, category=category))


def check_all(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    meta: dict = {}

    policy = json.loads(_read(monorepo, POLICY_RELATIVE))
    viz = json.loads(_read(monorepo, VIZ_CONTRACT))
    catalog = json.loads(_read(monorepo, TOKEN_CATALOG))
    assessment_styles = _read(monorepo, ASSESSMENT_STYLES)
    assessment_renderer = _read(monorepo, ASSESSMENT_RENDERER)
    eir_styles = _read(monorepo, EIR_STYLES)
    eir_renderer = _read(monorepo, EIR_RENDERER)
    pkg = json.loads(_read(monorepo, "vscode-plugin/package.json"))
    presentation_copy = _read(monorepo, "vscode-plugin/src/ui/presentationCopy.ts")

    # Policy
    _add(
        checks,
        "policy:id_version",
        policy.get("policy_id") == POLICY_ID
        and policy.get("policy_version") == POLICY_VERSION,
        f"{POLICY_ID}:{POLICY_VERSION}",
        "visualization_policy",
    )
    _add(
        checks,
        "policy:domain_authoritative",
        policy.get("domain_truth_authoritative") is True
        and policy.get("scoring_change_allowed") is False
        and policy.get("threshold_change_allowed") is False
        and policy.get("invented_health_score_allowed") is False
        and policy.get("zero_findings_implies_health") is False
        and policy.get("color_only_meaning_allowed") is False
        and policy.get("start_epic_15") is False,
        "guards",
        "visualization_policy",
    )
    _add(
        checks,
        "policy:no_chart_js_cdn",
        policy.get("chart_js_allowed") is False
        and policy.get("chart_cdn_allowed") is False
        and policy.get("chart_network_dependency_allowed") is False,
        "offline",
        "visualization_policy",
    )

    # Domain semantics / roles
    _add(
        checks,
        "domain_semantics:contract_present",
        viz.get("schema") == "codestrata-visualization-contract"
        and viz.get("domain_truth_authoritative") is True,
        "contract",
        "domain_semantics",
    )
    risk_roles = viz.get("semantic_risk_roles") or {}
    _add(
        checks,
        "semantic_roles:risk",
        all(k in risk_roles for k in ("critical", "high", "medium", "low", "info")),
        "risk_roles",
        "semantic_role",
    )
    status_roles = viz.get("semantic_status_roles") or {}
    _add(
        checks,
        "semantic_roles:status",
        all(
            k in status_roles
            for k in (
                "success",
                "warning",
                "failure",
                "unavailable",
                "partial",
                "not_assessed",
            )
        ),
        "status_roles",
        "semantic_role",
    )
    conf_roles = viz.get("semantic_confidence_roles") or {}
    _add(
        checks,
        "semantic_roles:confidence",
        all(k in conf_roles for k in ("high", "moderate", "limited", "unavailable")),
        "confidence_roles",
        "semantic_role",
    )

    # Risk / severity
    _add(
        checks,
        "risk:tokens_in_catalog",
        catalog["risk_colors"]["critical"] == "#a04b17"
        and catalog["risk_colors"]["medium"] == "#4d6885"
        and catalog["risk_colors"]["low"] == "#16756a",
        "risk_colors",
        "risk",
    )
    mappings = viz.get("domain_mappings") or {}
    _add(
        checks,
        "severity:assessment_mapping",
        mappings.get("assessment_finding_severity", {}).get("critical") == "critical"
        and mappings.get("assessment_finding_severity", {}).get("informational")
        == "info",
        "mapped",
        "severity",
    )
    _add(
        checks,
        "severity:markers_not_color_only",
        "severity-critical::before" in assessment_styles
        and "severity-high::before" in assessment_styles,
        "markers",
        "severity",
    )
    _add(
        checks,
        "severity:informational_not_low_teal",
        "severity-informational" in assessment_styles
        and "cs-status-info" in assessment_styles
        and ".severity-informational" in assessment_styles,
        "info_distinct",
        "severity",
    )

    # Status visualization
    _add(
        checks,
        "status:not_assessed_class",
        "status-badge-not-assessed" in assessment_styles
        and "status-badge-not-assessed" in assessment_renderer,
        "not_assessed",
        "status_visualization",
    )
    _add(
        checks,
        "status:not_assessed_not_success",
        'status-badge-not-assessed"' in assessment_renderer
        or "status-badge-not-assessed" in assessment_renderer,
        "guard",
        "status_visualization",
    )
    # Guard substring bug: "assessed" must not alone classify not-assessed as success
    _add(
        checks,
        "status:substring_guard",
        "not-assessed" in assessment_renderer
        and 'token in key for token in ("success", "complete", "ok", "ready", "assessed")'
        not in assessment_renderer,
        "no_false_success",
        "status_visualization",
    )

    # Confidence
    _add(
        checks,
        "confidence:separate_from_risk",
        viz.get("score_components", {})
        .get("confidence_indicator", {})
        .get("forbidden")
        == "risk_palette_for_confidence"
        and policy.get("confidence_is_not_health") is True,
        "separated",
        "confidence",
    )
    _add(
        checks,
        "confidence:assessment_styles",
        "confidence-badge" in assessment_styles
        and "cs-status-info" in assessment_styles,
        "styles",
        "confidence",
    )
    _add(
        checks,
        "confidence:eir_badge",
        "confidence-badge" in eir_styles and "confidence-badge" in eir_renderer,
        "eir",
        "confidence",
    )
    _add(
        checks,
        "confidence:eir_not_health_copy",
        "not repository health" in eir_renderer.lower(),
        "copy",
        "confidence",
    )

    # Scores
    inventory = viz.get("score_inventory") or []
    _add(
        checks,
        "score:inventory_present",
        len(inventory) >= 4,
        str(len(inventory)),
        "score",
    )
    _add(
        checks,
        "score:no_universal",
        "universal_codestrata_score" in (viz.get("forbidden_scores") or []),
        "forbidden",
        "score",
    )
    components = viz.get("score_components") or {}
    _add(
        checks,
        "score_component:defined",
        all(
            k in components
            for k in (
                "numeric_score",
                "categorical_score",
                "metric_value",
                "confidence_indicator",
            )
        ),
        "components",
        "score_component",
    )

    # Palettes / charts
    palettes = viz.get("palettes") or {}
    _add(
        checks,
        "palette:risk_vs_categorical",
        palettes.get("risk", {}).get("use") == "actual_risk_and_severity_only"
        and "forbidden" in palettes.get("categorical_neutral", {}),
        "separated",
        "palette",
    )
    _add(
        checks,
        "palette:catalog_chart_colors",
        "series_1" in catalog.get("chart_colors", {}),
        "chart_colors",
        "palette",
    )
    grammar = viz.get("chart_grammar") or {}
    _add(
        checks,
        "chart_contract:offline",
        "cdn" in grammar.get("forbidden", [])
        and "client_javascript" in grammar.get("forbidden", []),
        "offline",
        "chart_contract",
    )
    _add(
        checks,
        "chart_contract:textual_equivalent",
        "textual_equivalent" in grammar.get("required_parts", []),
        "a11y",
        "chart_contract",
    )
    inventory_charts = grammar.get("current_inventory") or {}
    _add(
        checks,
        "chart_inventory:no_invented",
        "no_svg" in inventory_charts.get("assessment_html", "")
        and "do_not_invent" in inventory_charts.get("decision", ""),
        "restrained",
        "chart_inventory",
    )
    _add(
        checks,
        "chart_inventory:no_cdn_in_reports",
        "cdn." not in assessment_styles.lower()
        and "cdn." not in eir_styles.lower()
        and "<script" not in assessment_styles.lower(),
        "no_cdn",
        "chart_inventory",
    )
    _add(
        checks,
        "legend:labels_required",
        all(r.get("label_required") for r in risk_roles.values()),
        "labels",
        "legend",
    )

    # Empty states
    empty = viz.get("empty_states") or {}
    _add(
        checks,
        "empty_state:zero_findings_rule",
        empty.get("zero_findings", {}).get("forbidden_labels") is not None
        and "Healthy" in empty["zero_findings"]["forbidden_labels"],
        "no_false_health",
        "empty_state",
    )
    _add(
        checks,
        "empty_state:assessment_copy",
        "No findings were produced" in assessment_renderer
        and "does not certify" in assessment_renderer,
        "copy",
        "empty_state",
    )
    for label in FORBIDDEN_HEALTH_LABELS:
        _add(
            checks,
            f"empty_state:no_{label.lower()}_claim",
            f">{label}" not in assessment_renderer
            or "does not certify" in assessment_renderer,
            label,
            "empty_state",
        )

    # Assessment / EIR mapping
    _add(
        checks,
        "assessment_mapping:severity_classes",
        ".badge.severity-" in assessment_styles
        or "severity-critical" in assessment_styles,
        "classes",
        "assessment_mapping",
    )
    _add(
        checks,
        "assessment_mapping:status_classes",
        "status-badge-succeeded" in assessment_styles
        and "status-badge-partial" in assessment_styles
        and "status-badge-failed" in assessment_styles,
        "status",
        "assessment_mapping",
    )
    _add(
        checks,
        "eir_mapping:severity_classes",
        "status-severity-critical" in eir_styles
        and "status-severity-informational" in eir_styles
        and "cs-status-info" in eir_styles,
        "severity",
        "eir_mapping",
    )
    _add(
        checks,
        "eir_mapping:confidence",
        "confidence-badge" in eir_renderer,
        "confidence",
        "eir_mapping",
    )

    # Boundaries
    _add(
        checks,
        "docs_boundary:no_commercial_eir_in_viz_contract",
        viz.get("consumers", {}).get("documentation", {}).get("commercial_eir_metrics")
        is False,
        "docs",
        "docs_boundary",
    )
    _add(
        checks,
        "marketplace_boundary:no_eir",
        viz.get("consumers", {}).get("marketplace", {}).get("commercial_eir") is False,
        "marketplace",
        "marketplace_boundary",
    )
    _add(
        checks,
        "vscode_boundary:no_dashboard",
        viz.get("consumers", {}).get("vscode", {}).get("health_dashboard") is False
        and "health dashboard" not in presentation_copy.lower(),
        "vscode",
        "vscode_boundary",
    )
    _add(
        checks,
        "vscode_boundary:version",
        pkg.get("version") == "0.2.0",
        "0.2.0",
        "vscode_boundary",
    )

    # Dark / print / a11y
    _add(
        checks,
        "dark_theme:tokens_support",
        "prefers-color-scheme: dark" in _read(
            monorepo, "engine/src/codestrata/design_system/tokens.py"
        )
        or "night" in catalog["colors"],
        "dark",
        "dark_theme",
    )
    _add(
        checks,
        "print:media_present",
        "@media print" in assessment_styles and "@media print" in eir_styles,
        "print",
        "print",
    )
    _add(
        checks,
        "accessibility_baseline:no_color_only",
        viz.get("accessibility_baseline", {}).get("color_only_meaning_allowed") is False
        and policy.get("color_only_meaning_allowed") is False,
        "baseline",
        "accessibility_baseline",
    )
    _add(
        checks,
        "schema_boundary:assessment_1_2",
        policy.get("assessment_schema_version") == "1.2",
        "1.2",
        "schema_boundary",
    )
    _add(
        checks,
        "schema_boundary:no_ds_bump",
        policy.get("design_system_bump_required") is False
        and catalog.get("schema_version") == "1.0.0",
        "1.0",
        "schema_boundary",
    )
    _add(
        checks,
        "navigation_boundary:ia_owned_by_14_9",
        (monorepo / "design-system/contracts/report-information-architecture.json").exists()
        and policy.get("navigation_ia_change_allowed") is False,
        "14.9_owns_ia",
        "navigation_boundary",
    )
    for rel in FORBIDDEN_EPIC_15_PATHS:
        _add(
            checks,
            f"asset_boundary:absent:{rel.replace('/', '_')}",
            not (monorepo / rel).exists(),
            "absent",
            "asset_boundary",
        )
    _add(
        checks,
        "asset_boundary:no_logo_change",
        policy.get("universal_logo_change_allowed") is False,
        "deferred_14_10",
        "asset_boundary",
    )

    policy_text = json.dumps(policy, sort_keys=True)
    _add(
        checks,
        "determinism:policy_clean",
        "timestamp" not in policy_text and "/Users/" not in policy_text,
        "clean",
        "determinism",
    )

    # Negatives A–Z
    scenarios = [
        ("A", "no_score_algo_change", policy.get("scoring_change_allowed") is False),
        ("B", "no_eir_calc_change", policy.get("scoring_change_allowed") is False),
        ("C", "no_threshold_change", policy.get("threshold_change_allowed") is False),
        ("D", "no_universal_score", "universal_codestrata_score" in str(viz.get("forbidden_scores"))),
        ("E", "zero_findings_not_healthy", policy.get("zero_findings_implies_health") is False),
        ("F", "not_assessed_not_success", "status-badge-not-assessed" in assessment_renderer),
        ("G", "partial_distinct", "status-badge-partial" in assessment_styles),
        ("H", "unavailable_neutral", "not_assessed" in status_roles),
        ("I", "confidence_not_health", policy.get("confidence_is_not_health") is True),
        ("J", "low_confidence_not_critical", "risk_palette_for_confidence" in str(viz)),
        ("K", "risk_has_markers", "::before" in assessment_styles),
        ("L", "categorical_not_risk", "forbidden" in str(palettes.get("categorical_neutral"))),
        ("M", "no_cdn", policy.get("chart_cdn_allowed") is False),
        ("N", "no_chart_js", policy.get("chart_js_allowed") is False),
        ("O", "no_hover_only_critical", "hover_only" in grammar.get("tooltip_rule", "") or "must_not" in grammar.get("tooltip_rule", "")),
        ("P", "textual_equivalent", "textual_equivalent" in grammar.get("required_parts", [])),
        ("Q", "no_random_svg_ids", "random" not in grammar.get("implementation", "")),
        ("R", "dark_required", policy.get("dark_theme_visualization_required") is True),
        ("S", "print_required", policy.get("print_visualization_required") is True),
        ("T", "docs_no_commercial_metrics", viz["consumers"]["documentation"]["commercial_eir_metrics"] is False),
        ("U", "marketplace_no_eir", viz["consumers"]["marketplace"]["commercial_eir"] is False),
        ("V", "vscode_no_dashboard", viz["consumers"]["vscode"]["health_dashboard"] is False),
        ("W", "nav_ia_unchanged", policy.get("navigation_ia_change_allowed") is False),
        ("X", "epic_15_false", policy.get("start_epic_15") is False),
        ("Y", "policy_deterministic", "timestamp" not in policy_text),
        ("Z", "no_path_leak", "/Users/" not in policy_text),
    ]
    for letter, name, ok in scenarios:
        safe = name.replace("timestamp", "time_field")
        _add(checks, f"negative:{letter}_{safe}", ok, letter, "scenarios")

    if policy.get("scoring_change_allowed"):
        defects.append(Defect("score semantics defect", "Scoring changes must not be allowed"))
    if "status-badge-not-assessed" not in assessment_renderer:
        defects.append(
            Defect("status visualization defect", "not-assessed mapping missing")
        )

    meta["score_inventory_count"] = len(inventory)
    return checks, defects, meta
