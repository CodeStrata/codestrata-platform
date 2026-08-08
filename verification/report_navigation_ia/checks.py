"""Slice 14.9 checks — report navigation and information architecture.

Presentation/IA only. Domain truth, schemas, scoring, and visualization
semantics are read as boundaries, never rewritten.
"""

from __future__ import annotations

import json
import re
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from verification.report_navigation_ia.contract import (
    ASSESSMENT_BUILDER,
    ASSESSMENT_HEADS,
    ASSESSMENT_LEGACY_ALIASES,
    ASSESSMENT_RENDERER,
    ASSESSMENT_SECTION_ORDER,
    ASSESSMENT_STABLE_ANCHORS,
    ASSESSMENT_STYLES,
    EIR_DEMO_CATALOG,
    EIR_RENDERER,
    EIR_SECTION_ORDER,
    EIR_SECTIONS,
    EIR_STYLES,
    FORBIDDEN_15_7_PATHS,
    IA_CONTRACT,
    POLICY_ID,
    POLICY_RELATIVE,
    POLICY_VERSION,
    PRESENTATION_POLICY,
    VIZ_CONTRACT,
)
from verification.report_navigation_ia.models import CheckResult, Defect

_ID_RE = re.compile(r'(?<![\w-])id="([^"]+)"')
_HREF_RE = re.compile(r'href="#([^"]+)"')
_HEADING_RE = re.compile(r"<h([1-6])\b")
_SECTION_ID_RE = re.compile(r'<section[^>]*(?<![\w-])id="([^"]+)"', re.IGNORECASE)
_TOC_RE = re.compile(r"<nav[^>]*class=\"toc\"[^>]*>(.*?)</nav>", re.IGNORECASE | re.DOTALL)
_KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_TIMESTAMP_RE = re.compile(r"(19|20)\d{2}-\d{2}-\d{2}|\d{10,}")

_ALLOWED_ROLES = frozenset(
    {
        "report_identity",
        "orientation",
        "executive_summary",
        "primary_analysis",
        "secondary_analysis",
        "finding_detail",
        "evidence_detail",
        "recommendation_detail",
        "supporting_detail",
        "technical_appendix",
        "report_metadata",
        "limitations",
        "navigation",
    }
)


def _add(checks: list[CheckResult], name: str, ok: bool, detail: str, category: str) -> None:
    checks.append(CheckResult(name=name, ok=bool(ok), detail=detail, category=category))


def _read_json(monorepo: Path, relative: str) -> dict[str, Any]:
    return json.loads((monorepo / relative).read_text(encoding="utf-8"))


def _read_text(monorepo: Path, relative: str) -> str:
    return (monorepo / relative).read_text(encoding="utf-8")


def render_assessment_html() -> str:
    """Render a deterministic synthetic Assessment report (no customer data)."""

    from codestrata.reporting.html_v2 import HtmlReportRenderer, build_html_report_view_model
    from verification.assessment_report_redesign.fixtures import synthetic_report_input

    with tempfile.TemporaryDirectory() as tmp:
        return HtmlReportRenderer().render(
            build_html_report_view_model(synthetic_report_input(Path(tmp)))
        )


def render_eir_html(monorepo: Path) -> str:
    """Render the deterministic OSS demonstration website-safe EIR export."""

    from codestrata_platform.intelligence_reporting.application.oss_demonstration import (
        build_oss_demonstration_report,
    )
    from codestrata_platform.intelligence_reporting.presentation.static_html.renderer import (
        render_website_safe_html,
    )

    result = build_oss_demonstration_report(catalog_path=monorepo / EIR_DEMO_CATALOG)
    return render_website_safe_html(result.export_bundle.document)


def _heading_levels(html: str) -> list[int]:
    return [int(value) for value in _HEADING_RE.findall(html)]


def _heading_skips(levels: list[int]) -> list[tuple[int, int]]:
    return [
        (levels[index - 1], levels[index])
        for index in range(1, len(levels))
        if levels[index] > levels[index - 1] + 1
    ]


def _toc_links(html: str) -> list[str]:
    match = _TOC_RE.search(html)
    if match is None:
        return []
    return _HREF_RE.findall(match.group(1))


def _ordered_ids(html: str, wanted: tuple[str, ...]) -> list[str]:
    positions: list[tuple[int, str]] = []
    for anchor in wanted:
        index = html.find(f'id="{anchor}"')
        if index >= 0:
            positions.append((index, anchor))
    return [anchor for _, anchor in sorted(positions)]


def check_all(  # noqa: PLR0915 - single deterministic check surface
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    meta: dict[str, Any] = {}

    policy = _read_json(monorepo, POLICY_RELATIVE)
    ia = _read_json(monorepo, IA_CONTRACT)
    viz = _read_json(monorepo, VIZ_CONTRACT)
    presentation_policy = _read_json(monorepo, PRESENTATION_POLICY)

    assessment_renderer = _read_text(monorepo, ASSESSMENT_RENDERER)
    assessment_builder = _read_text(monorepo, ASSESSMENT_BUILDER)
    assessment_styles = _read_text(monorepo, ASSESSMENT_STYLES)
    assessment_heads_source = _read_text(monorepo, ASSESSMENT_HEADS)
    eir_renderer = _read_text(monorepo, EIR_RENDERER)
    eir_sections = _read_text(monorepo, EIR_SECTIONS)
    eir_styles = _read_text(monorepo, EIR_STYLES)

    assessment_html = render_assessment_html()
    eir_html = render_eir_html(monorepo)

    # ------------------------------------------------------------------ policy
    _add(
        checks,
        "ia_policy:identity",
        policy.get("policy_id") == POLICY_ID and policy.get("policy_version") == POLICY_VERSION,
        "identity",
        "ia_policy",
    )
    _add(
        checks,
        "ia_policy:domain_truth",
        policy.get("domain_truth_authoritative") is True
        and policy.get("content_generation_change_allowed") is False
        and policy.get("schema_change_allowed") is False,
        "domain_truth",
        "ia_policy",
    )
    _add(
        checks,
        "ia_policy:navigation_rules",
        policy.get("navigation_javascript_allowed") is False
        and policy.get("navigation_network_dependency_allowed") is False
        and policy.get("global_breadcrumbs_allowed") is False
        and policy.get("dead_navigation_link_allowed") is False,
        "navigation",
        "ia_policy",
    )
    _add(
        checks,
        "ia_policy:structure_rules",
        policy.get("stable_anchor_preservation_required") is True
        and policy.get("executive_orientation_required") is True
        and policy.get("deterministic_section_order_required") is True
        and policy.get("section_reorder_allowed") is False
        and policy.get("mobile_navigation_required") is True
        and policy.get("print_navigation_required") is True,
        "structure",
        "ia_policy",
    )
    _add(
        checks,
        "ia_policy:boundaries",
        policy.get("commercial_boundary_required") is True
        and policy.get("report_products_remain_distinct") is True
        and policy.get("visualization_semantics_change_allowed") is False
        and policy.get("universal_asset_change_allowed") is False
        and policy.get("accessibility_certification_claimed") is False
        and policy.get("documentation_deployment_complete") is True
        and policy.get("start_slice_15_7") is False,
        "boundaries",
        "ia_policy",
    )
    _add(
        checks,
        "ia_policy:versions",
        policy.get("design_system_version") == "1.0"
        and policy.get("visualization_policy_version") == "1.0"
        and policy.get("assessment_schema_version") == "1.2"
        and policy.get("extension_version") == "0.2.0"
        and policy.get("design_system_bump_required") is False,
        "versions",
        "ia_policy",
    )

    # --------------------------------------------------------------- hierarchy
    levels = ia.get("hierarchy_levels", {})
    _add(
        checks,
        "hierarchy:contract_identity",
        ia.get("schema") == "codestrata-report-information-architecture-contract"
        and ia.get("schema_version") == "1.0.0"
        and ia.get("policy") == f"{POLICY_ID}:{POLICY_VERSION}",
        "identity",
        "hierarchy",
    )
    _add(
        checks,
        "hierarchy:seven_levels",
        [str(index) for index in range(7)] == sorted(levels, key=int),
        "levels_0_6",
        "hierarchy",
    )
    _add(
        checks,
        "hierarchy:levels_answer_questions",
        all(
            isinstance(entry.get("question"), str) and entry.get("content")
            for entry in levels.values()
        ),
        "questions",
        "hierarchy",
    )
    _add(
        checks,
        "hierarchy:no_invented_content",
        levels.get("2", {}).get("invented_conclusions_allowed") is False
        and levels.get("5", {}).get("invented_priorities_or_timelines_allowed") is False,
        "no_generation",
        "hierarchy",
    )
    _add(
        checks,
        "hierarchy:products_distinct",
        ia.get("products_remain_distinct") is True
        and policy.get("shared_contract_is_structural_only") is True,
        "distinct",
        "hierarchy",
    )

    # -------------------------------------------------------- heading structure
    heading_rules = ia.get("heading_rules", {})
    _add(
        checks,
        "heading_structure:rules",
        heading_rules.get("h1") == "report_title_only"
        and heading_rules.get("h1_count") == 1
        and heading_rules.get("styling_only_headings_allowed") is False
        and heading_rules.get("arbitrary_skip_allowed") is False,
        "rules",
        "heading_structure",
    )
    for surface, html in (("assessment", assessment_html), ("eir", eir_html)):
        surface_levels = _heading_levels(html)
        _add(
            checks,
            f"heading_structure:{surface}_single_h1",
            surface_levels.count(1) == 1,
            f"h1={surface_levels.count(1)}",
            "heading_structure",
        )
        skips = _heading_skips(surface_levels)
        _add(
            checks,
            f"heading_structure:{surface}_no_skips",
            not skips,
            f"skips={len(skips)}",
            "heading_structure",
        )
        if skips:
            defects.append(
                Defect(
                    "heading hierarchy defect",
                    f"{surface} report skips heading levels",
                )
            )
    _add(
        checks,
        "heading_structure:assessment_sections_h2",
        '<div class="section-head"><h2>' in assessment_renderer,
        "h2_sections",
        "heading_structure",
    )
    _add(
        checks,
        "heading_structure:assessment_subsections_h3",
        '<div class="section-head"><h3>' in assessment_renderer,
        "h3_subsections",
        "heading_structure",
    )

    # --------------------------------------------------------- section headers
    anatomy = ia.get("section_header_anatomy", {})
    _add(
        checks,
        "section_header:anatomy",
        set(anatomy.get("required_parts", [])) == {"heading", "anchor"}
        and anatomy.get("status_or_metric_required_on_every_section") is False,
        "anatomy",
        "section_header",
    )
    _add(
        checks,
        "section_header:assessment_parts",
        'class="section-eyebrow"' in assessment_html and 'class="section-note"' in assessment_html,
        "eyebrow_note",
        "section_header",
    )
    _add(
        checks,
        "section_header:eyebrow_decorative",
        anatomy.get("eyebrow_decorative") is True
        and 'class="section-eyebrow" aria-hidden="true"' in assessment_renderer,
        "aria_hidden",
        "section_header",
    )
    _add(
        checks,
        "section_header:eir_descriptions",
        eir_html.count('<p class="muted">') >= 3,
        "descriptions",
        "section_header",
    )

    # ----------------------------------------------------------------- anchors
    anchor_rules = ia.get("anchor_rules", {})
    _add(
        checks,
        "anchors:rules",
        anchor_rules.get("random_ids_allowed") is False
        and anchor_rules.get("duplicate_ids_allowed") is False
        and anchor_rules.get("timestamp_in_id_allowed") is False
        and anchor_rules.get("removal_policy") == "preserve_or_alias",
        "rules",
        "anchors",
    )
    for surface, html in (("assessment", assessment_html), ("eir", eir_html)):
        ids = _ID_RE.findall(html)
        counts = Counter(ids)
        duplicates = sorted(key for key, count in counts.items() if count > 1)
        _add(
            checks,
            f"anchors:{surface}_unique",
            not duplicates,
            f"duplicates={len(duplicates)}",
            "anchors",
        )
        if duplicates:
            defects.append(
                Defect("anchor defect", f"{surface} report emits duplicate element ids")
            )
        section_ids = _SECTION_ID_RE.findall(html)
        non_kebab = sorted(sid for sid in section_ids if not _KEBAB_RE.match(sid))
        _add(
            checks,
            f"anchors:{surface}_section_kebab_case",
            not non_kebab,
            f"non_kebab={len(non_kebab)}",
            "anchors",
        )
        timestamped = sorted(sid for sid in section_ids if _TIMESTAMP_RE.search(sid))
        _add(
            checks,
            f"anchors:{surface}_no_time_based_ids",
            not timestamped,
            f"time_based={len(timestamped)}",
            "anchors",
        )
        meta[f"{surface}_id_count"] = len(ids)

    missing_stable = [
        anchor
        for anchor in ASSESSMENT_STABLE_ANCHORS
        if f'id="{anchor}"' not in assessment_html
    ]
    _add(
        checks,
        "anchors:assessment_stable_present",
        not missing_stable,
        f"missing={len(missing_stable)}",
        "anchors",
    )
    if missing_stable:
        defects.append(
            Defect("stable anchor defect", "assessment stable anchors missing from report")
        )
    contract_aliases = set(ia["assessment_report"]["legacy_anchor_aliases"])
    _add(
        checks,
        "anchors:assessment_legacy_aliases_retained",
        all(alias in assessment_heads_source for alias in ASSESSMENT_LEGACY_ALIASES)
        and contract_aliases == set(ASSESSMENT_LEGACY_ALIASES)
        and "_render_legacy_pack_section_alias" in assessment_renderer,
        "aliases",
        "anchors",
    )
    missing_eir = [
        key for key in EIR_SECTION_ORDER if f'id="section-{key}"' not in eir_html
    ]
    _add(
        checks,
        "anchors:eir_sections_present",
        not missing_eir,
        f"missing={len(missing_eir)}",
        "anchors",
    )

    # -------------------------------------------------------------- deep links
    for surface, html in (("assessment", assessment_html), ("eir", eir_html)):
        counts = Counter(_ID_RE.findall(html))
        targets = sorted({href for href in _HREF_RE.findall(html) if href not in counts})
        _add(
            checks,
            f"deep_link:{surface}_resolve",
            not targets,
            f"unresolved={len(targets)}",
            "deep_link",
        )
        if targets:
            defects.append(
                Defect("navigation defect", f"{surface} report has unresolved internal links")
            )
    _add(
        checks,
        "deep_link:assessment_entity_prefixes",
        all(
            prefix in str(ia["assessment_report"]["entity_anchor_prefixes"])
            for prefix in ("finding-", "recommendation-", "evidence-")
        ),
        "prefixes",
        "deep_link",
    )

    # --------------------------------------------------------------------- toc
    assessment_toc = _toc_links(assessment_html)
    eir_toc = _toc_links(eir_html)
    assessment_ids = Counter(_ID_RE.findall(assessment_html))
    eir_ids = Counter(_ID_RE.findall(eir_html))
    _add(
        checks,
        "toc:assessment_present",
        'id="contents"' in assessment_html
        and 'aria-label="Table of contents"' in assessment_html
        and bool(assessment_toc),
        f"entries={len(assessment_toc)}",
        "toc",
    )
    _add(
        checks,
        "toc:assessment_links_resolve",
        all(link in assessment_ids for link in assessment_toc),
        "resolve",
        "toc",
    )
    _add(
        checks,
        "toc:assessment_major_sections_only",
        not any(link.startswith(("finding-", "evidence-")) for link in assessment_toc),
        "major_only",
        "toc",
    )
    _add(
        checks,
        "toc:assessment_presence_driven",
        "rendered_heads" in assessment_builder
        and "presence-driven" in assessment_builder,
        "presence_driven",
        "toc",
    )
    _add(
        checks,
        "toc:eir_present",
        'aria-label="Table of contents"' in eir_html and bool(eir_toc),
        f"entries={len(eir_toc)}",
        "toc",
    )
    _add(
        checks,
        "toc:eir_links_resolve",
        all(link in eir_ids for link in eir_toc),
        "resolve",
        "toc",
    )
    _add(
        checks,
        "toc:single_navigation_per_report",
        len(_TOC_RE.findall(assessment_html)) == 1 and len(_TOC_RE.findall(eir_html)) == 1,
        "single_nav",
        "toc",
    )
    _add(
        checks,
        "toc:no_breadcrumbs",
        ia["navigation"]["breadcrumbs"]["enabled"] is False
        and "breadcrumb" not in assessment_html.lower()
        and "breadcrumb" not in eir_html.lower(),
        "no_breadcrumbs",
        "toc",
    )
    _add(
        checks,
        "toc:no_javascript",
        "<script" not in assessment_html.lower()
        and "<script" not in eir_html.lower()
        and ia["navigation"]["javascript_required"] is False,
        "no_js",
        "toc",
    )
    meta["assessment_toc_entries"] = len(assessment_toc)
    meta["eir_toc_entries"] = len(eir_toc)

    # ------------------------------------------------------- assessment mapping
    assessment_sections = ia["assessment_report"]["sections"]
    bad_roles = [
        entry["anchor"] for entry in assessment_sections if entry["role"] not in _ALLOWED_ROLES
    ]
    _add(
        checks,
        "assessment_mapping:roles_valid",
        not bad_roles,
        f"invalid={len(bad_roles)}",
        "assessment_mapping",
    )
    missing_mapped = [
        entry["anchor"]
        for entry in assessment_sections
        if not entry.get("conditional") and f'id="{entry["anchor"]}"' not in assessment_html
    ]
    _add(
        checks,
        "assessment_mapping:sections_rendered",
        not missing_mapped,
        f"missing={len(missing_mapped)}",
        "assessment_mapping",
    )
    mapped_heads = ia["assessment_report"]["subsections"]["anchors"]
    _add(
        checks,
        "assessment_mapping:head_subsections",
        all(f'id="{anchor}"' in assessment_html for anchor in mapped_heads)
        and ia["assessment_report"]["subsections"]["heading"] == "h3",
        "heads",
        "assessment_mapping",
    )
    _add(
        checks,
        "assessment_mapping:order_authority_referenced",
        "EXPECTED_SECTION_ORDER" in ia["assessment_report"]["order_authority"],
        "authority",
        "assessment_mapping",
    )

    # -------------------------------------------------------------- eir mapping
    eir_sections_map = ia["eir"]["sections"]
    bad_eir_roles = [
        entry["anchor"] for entry in eir_sections_map if entry["role"] not in _ALLOWED_ROLES
    ]
    _add(
        checks,
        "eir_mapping:roles_valid",
        not bad_eir_roles,
        f"invalid={len(bad_eir_roles)}",
        "eir_mapping",
    )
    missing_eir_mapped = [
        entry["anchor"]
        for entry in eir_sections_map
        if entry["anchor"] != "cover" and f'id="{entry["anchor"]}"' not in eir_html
    ]
    _add(
        checks,
        "eir_mapping:sections_rendered",
        not missing_eir_mapped,
        f"missing={len(missing_eir_mapped)}",
        "eir_mapping",
    )
    _add(
        checks,
        "eir_mapping:order_authority_referenced",
        "SECTION_ORDER" in ia["eir"]["order_authority"] and "SECTION_ORDER" in eir_sections,
        "authority",
        "eir_mapping",
    )
    _add(
        checks,
        "eir_mapping:disclosure_rules",
        ia["eir"]["disclosure"]["element"] == "details"
        and "confidence_level" in ia["eir"]["disclosure"]["always_visible"]
        and "<details" in eir_html,
        "details",
        "eir_mapping",
    )

    # -------------------------------------------------------- executive summary
    exec_index = assessment_html.find('id="executive-summary"')
    results_index = assessment_html.find('id="assessment-results"')
    appendix_index = assessment_html.find('id="technical-appendix"')
    _add(
        checks,
        "executive_summary:assessment_before_analysis",
        0 <= exec_index < results_index < appendix_index,
        "ordering",
        "executive_summary",
    )
    _add(
        checks,
        "executive_summary:assessment_single",
        assessment_html.count('id="executive-summary"') == 1
        and policy.get("duplicate_executive_summary_allowed") is False,
        "single",
        "executive_summary",
    )
    eir_orientation = eir_html.find('id="section-orientation"')
    eir_capability = eir_html.find('id="section-capability"')
    eir_methodology = eir_html.find('id="section-methodology"')
    _add(
        checks,
        "executive_summary:eir_orientation_first",
        0 <= eir_orientation < eir_capability < eir_methodology,
        "ordering",
        "executive_summary",
    )
    _add(
        checks,
        "executive_summary:eir_structured_not_narrative",
        "Structured orientation only" in eir_html,
        "structured",
        "executive_summary",
    )

    # ---------------------------------------------------------------- metadata
    _add(
        checks,
        "metadata:assessment_placement",
        ia["assessment_report"]["metadata_placement"]["primary"] == "cover"
        and 'id="cover"' in assessment_html
        and "technical-appendix" in ia["assessment_report"]["metadata_placement"]["secondary"],
        "placement",
        "metadata",
    )
    _add(
        checks,
        "metadata:eir_placement",
        ia["eir"]["metadata_placement"]["primary"] == "cover"
        and 'class="cover-meta"' in eir_html
        and 'id="section-metadata"' in eir_html,
        "placement",
        "metadata",
    )
    _add(
        checks,
        "metadata:no_new_fields",
        policy.get("content_generation_change_allowed") is False,
        "no_new_fields",
        "metadata",
    )

    # -------------------------------------------------------- findings/evidence
    relationship = ia["assessment_report"]["findings_evidence_relationship"]
    _add(
        checks,
        "findings_evidence:assessment_relationship",
        relationship["cross_reference_required"] is True
        and relationship["evidence_detail_location"] == "technical-appendix",
        "relationship",
        "findings_evidence",
    )
    _add(
        checks,
        "findings_evidence:assessment_links",
        'href="#finding-' in assessment_html or 'id="finding-' in assessment_html,
        "finding_anchors",
        "findings_evidence",
    )
    _add(
        checks,
        "findings_evidence:eir_projection_respected",
        ia["eir"]["evidence_projection"]["raw_evidence_included"] is False
        and ia["eir"]["evidence_projection"]["reintroduce_raw_evidence_allowed"] is False
        and 'id="evidence-' not in eir_html,
        "projection",
        "findings_evidence",
    )
    _add(
        checks,
        "findings_evidence:eir_traceability_bounded",
        'id="section-drilldowns"' in eir_html
        and "Bounded navigation subsets" in eir_html,
        "bounded",
        "findings_evidence",
    )

    # --------------------------------------------------------- recommendations
    placement = ia["assessment_report"]["recommendation_placement"]
    _add(
        checks,
        "recommendation:placement_rule",
        placement["detail"] == "priority-actions"
        and placement["duplicate_full_content_allowed"] is False,
        "placement",
        "recommendation",
    )
    _add(
        checks,
        "recommendation:head_reference_only",
        "View recommendation details" in assessment_renderer,
        "reference_link",
        "recommendation",
    )
    recommendation_ids = [
        anchor
        for anchor in _ID_RE.findall(assessment_html)
        if anchor.startswith("recommendation-")
    ]
    _add(
        checks,
        "recommendation:no_duplicate_detail_anchors",
        len(recommendation_ids) == len(set(recommendation_ids)),
        f"anchors={len(recommendation_ids)}",
        "recommendation",
    )
    _add(
        checks,
        "recommendation:eir_observations_not_prescriptions",
        any(
            entry["anchor"] == "section-observations"
            and entry.get("note") == "observations_not_prescriptions"
            for entry in eir_sections_map
        ),
        "observations",
        "recommendation",
    )

    # -------------------------------------------------------- supporting detail
    _add(
        checks,
        "supporting_detail:assessment_appendix_last",
        appendix_index == max(
            assessment_html.find(f'id="{anchor}"') for anchor in ASSESSMENT_SECTION_ORDER
        ),
        "appendix_last",
        "supporting_detail",
    )
    _add(
        checks,
        "supporting_detail:eir_tail_sections",
        eir_html.find('id="section-methodology"') < eir_html.find('id="section-metadata"'),
        "tail",
        "supporting_detail",
    )
    _add(
        checks,
        "supporting_detail:no_generic_table_appendix",
        "All Tables" not in assessment_html and "All Tables" not in eir_html,
        "no_table_dump",
        "supporting_detail",
    )
    _add(
        checks,
        "supporting_detail:density_rules",
        ia["density"]["dashboard_card_conversion_allowed"] is False
        and ia["density"]["character"] == "evidence_oriented_technical_documentation",
        "density",
        "supporting_detail",
    )

    # ---------------------------------------------------------- empty sections
    empty_rules = ia["empty_sections"]
    _add(
        checks,
        "empty_section:rules",
        empty_rules["navigation_may_link_absent_section"] is False
        and empty_rules["fabricated_content_to_preserve_nav_allowed"] is False,
        "rules",
        "empty_section",
    )
    _add(
        checks,
        "empty_section:state_authority_is_visualization",
        empty_rules["state_authority"] == VIZ_CONTRACT,
        "authority",
        "empty_section",
    )
    _add(
        checks,
        "empty_section:eir_states_rendered",
        'class="empty-state"' in eir_html or "empty-state" in eir_styles,
        "eir_states",
        "empty_section",
    )
    _add(
        checks,
        "empty_section:assessment_not_assessed_distinct",
        "status-badge-not-assessed" in assessment_styles,
        "not_assessed",
        "empty_section",
    )

    # ------------------------------------------------------------ section order
    contract_assessment_order = tuple(
        entry["anchor"]
        for entry in assessment_sections
        if entry["anchor"] in ASSESSMENT_SECTION_ORDER
    )
    _add(
        checks,
        "section_order:assessment_contract_matches_authority",
        contract_assessment_order == ASSESSMENT_SECTION_ORDER,
        "contract",
        "section_order",
    )
    rendered_assessment_order = _ordered_ids(assessment_html, ASSESSMENT_SECTION_ORDER)
    expected_assessment_order = [
        anchor for anchor in ASSESSMENT_SECTION_ORDER if anchor in rendered_assessment_order
    ]
    _add(
        checks,
        "section_order:assessment_rendered",
        rendered_assessment_order == expected_assessment_order,
        "rendered",
        "section_order",
    )
    rendered_eir_order = _ordered_ids(
        eir_html, tuple(f"section-{key}" for key in EIR_SECTION_ORDER)
    )
    expected_eir_order = [
        f"section-{key}" for key in EIR_SECTION_ORDER if f"section-{key}" in rendered_eir_order
    ]
    _add(
        checks,
        "section_order:eir_rendered",
        rendered_eir_order == expected_eir_order,
        "rendered",
        "section_order",
    )
    _add(
        checks,
        "section_order:no_reorder_allowed",
        policy.get("section_reorder_allowed") is False,
        "frozen",
        "section_order",
    )
    if rendered_assessment_order != expected_assessment_order:
        defects.append(Defect("section order defect", "assessment section order changed"))

    # ------------------------------------------------- responsive navigation
    mobile = ia["navigation"]["mobile"]
    _add(
        checks,
        "responsive_navigation:contract",
        mobile["side_rail_allowed"] is False
        and set(mobile["breakpoints"]) == {"1024px", "820px", "560px"},
        "contract",
        "responsive_navigation",
    )
    for surface, styles in (("assessment", assessment_styles), ("eir", eir_styles)):
        _add(
            checks,
            f"responsive_navigation:{surface}_breakpoints",
            "@media (max-width: 1024px)" in styles
            and "@media (max-width: 820px)" in styles
            and "@media (max-width: 560px)" in styles,
            "breakpoints",
            "responsive_navigation",
        )
        _add(
            checks,
            f"responsive_navigation:{surface}_toc_static_on_mobile",
            "position: static" in styles,
            "static_toc",
            "responsive_navigation",
        )
    _add(
        checks,
        "responsive_navigation:sticky_desktop",
        "position: sticky" in assessment_styles and "position: sticky" in eir_styles,
        "sticky",
        "responsive_navigation",
    )

    # ----------------------------------------------------------- print navigation
    print_rules = ia["navigation"]["print"]
    _add(
        checks,
        "print_navigation:contract",
        print_rules["contents_retained"] is True and print_rules["links_readable"] is True,
        "contract",
        "print_navigation",
    )
    for surface, styles in (("assessment", assessment_styles), ("eir", eir_styles)):
        _add(
            checks,
            f"print_navigation:{surface}_print_layer",
            "@media print" in styles
            and ".skip-link, .report-product-bar" in styles,
            "print_layer",
            "print_navigation",
        )
        _add(
            checks,
            f"print_navigation:{surface}_toc_readable",
            "text-decoration: underline" in styles,
            "underline",
            "print_navigation",
        )

    # ------------------------------------------------------- commercial boundary
    commercial_markers = (
        'id="section-capability"',
        'id="section-drilldowns"',
        "Repository Drill-Downs",
        "Capability Comparison",
    )
    leaked = [marker for marker in commercial_markers if marker in assessment_html]
    _add(
        checks,
        "commercial_boundary:no_eir_sections_in_assessment",
        not leaked,
        f"leaked={len(leaked)}",
        "commercial_boundary",
    )
    if leaked:
        defects.append(
            Defect("commercial boundary defect", "EIR sections appear in Community Assessment")
        )
    assessment_only = ("assessment-results", "priority-actions", "technical-appendix")
    reverse_leak = [marker for marker in assessment_only if f'id="{marker}"' in eir_html]
    _add(
        checks,
        "commercial_boundary:no_assessment_sections_in_eir",
        not reverse_leak,
        f"leaked={len(reverse_leak)}",
        "commercial_boundary",
    )
    _add(
        checks,
        "commercial_boundary:eir_projection_statement",
        "Website-safe sanitized projection" in eir_html,
        "statement",
        "commercial_boundary",
    )
    docs_dir = monorepo / "docs"
    docs_leak = sorted(
        path.name
        for path in docs_dir.rglob("*.md")
        if "Capability Comparison" in path.read_text(encoding="utf-8")
        or "Repository Drill-Downs" in path.read_text(encoding="utf-8")
    )
    _add(
        checks,
        "commercial_boundary:community_docs_clean",
        not docs_leak,
        f"files={len(docs_leak)}",
        "commercial_boundary",
    )
    _add(
        checks,
        "commercial_boundary:contract_rules",
        ia["boundaries"]["eir_sections_in_assessment_allowed"] is False
        and ia["boundaries"]["assessment_sections_in_eir_allowed"] is False
        and ia["boundaries"]["commercial_navigation_in_community_docs_allowed"] is False,
        "rules",
        "commercial_boundary",
    )

    # ---------------------------------------------------- visualization boundary
    _add(
        checks,
        "visualization_boundary:contract_unchanged",
        viz.get("schema_version") == "1.0.0"
        and viz.get("policy") == "codestrata-visualization-policy:1.0",
        "unchanged",
        "visualization_boundary",
    )
    _add(
        checks,
        "visualization_boundary:status_semantics_intact",
        "status-badge-not-assessed" in assessment_renderer
        and "confidence-badge" in eir_renderer,
        "semantics",
        "visualization_boundary",
    )
    _add(
        checks,
        "visualization_boundary:no_semantics_change",
        policy.get("visualization_semantics_change_allowed") is False
        and ia["boundaries"]["visualization_semantics_change_allowed"] is False,
        "frozen",
        "visualization_boundary",
    )

    # ------------------------------------------------------------ asset boundary
    for relative in FORBIDDEN_15_7_PATHS:
        _add(
            checks,
            f"asset_boundary:absent:{relative.replace('/', '_')}",
            not (monorepo / relative).exists(),
            "absent",
            "asset_boundary",
        )
    _add(
        checks,
        "asset_boundary:complete_via_14_10",
        ia["boundaries"]["asset_redesign"] == "14.10"
        and policy.get("universal_asset_change_allowed") is False,
        "14.10",
        "asset_boundary",
    )

    # ---------------------------------------------------- accessibility boundary
    _add(
        checks,
        "accessibility_boundary:landmarks",
        'role="banner"' in assessment_html
        and 'role="main"' in assessment_html
        and "<main id=" in eir_html,
        "landmarks",
        "accessibility_boundary",
    )
    _add(
        checks,
        "accessibility_boundary:skip_links",
        'class="skip-link"' in assessment_html and 'class="skip-link"' in eir_html,
        "skip_links",
        "accessibility_boundary",
    )
    _add(
        checks,
        "accessibility_boundary:not_certified_here",
        policy.get("accessibility_certification_claimed") is False
        and ia["boundaries"]["accessibility_certification"] == "14.11",
        "14.11",
        "accessibility_boundary",
    )

    # ------------------------------------------------------- deployment boundary
    _add(
        checks,
        "deployment_boundary:14_12_complete",
        (monorepo / "verification/documentation_deployment").exists()
        and ia["boundaries"]["documentation_deployment"] == "14.12"
        and policy.get("documentation_deployment_complete") is True,
        "14_12_complete",
        "deployment_boundary",
    )

    # ----------------------------------------------------------- schema boundary
    engine_constants = _read_text(monorepo, "engine/src/codestrata/reporting/contract/constants.py")
    eir_policy_text = _read_text(
        monorepo,
        "platform/src/codestrata_platform/intelligence_reporting/"
        "application/website_export/policy.py",
    )
    _add(
        checks,
        "schema_boundary:assessment_1_2",
        'ASSESSMENT_JSON_SCHEMA_VERSION = "1.2"' in engine_constants
        and 'ASSESSMENT_JSON_REPORT_VERSION = "1.2"' in engine_constants,
        "1.2",
        "schema_boundary",
    )
    _add(
        checks,
        "schema_boundary:eir_export_unchanged",
        'WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION = "1.0"' in eir_policy_text
        and 'HTML_TEMPLATE_VERSION = "eir-static-html-v2"' in eir_policy_text,
        "unchanged",
        "schema_boundary",
    )
    _add(
        checks,
        "schema_boundary:presentation_policy_navigation_complete",
        presentation_policy.get("navigation_standardization_complete") is True
        and presentation_policy.get("design_system_bump_required") is False,
        "presentation_policy",
        "schema_boundary",
    )

    # -------------------------------------------------------------- determinism
    _add(
        checks,
        "determinism:assessment_render_stable",
        render_assessment_html() == assessment_html,
        "stable",
        "determinism",
    )
    _add(
        checks,
        "determinism:eir_render_stable",
        render_eir_html(monorepo) == eir_html,
        "stable",
        "determinism",
    )
    policy_text = json.dumps(policy, sort_keys=True)
    ia_text_value = json.dumps(ia, sort_keys=True)
    _add(
        checks,
        "determinism:artifacts_clean",
        "/Users/" not in policy_text
        and "/Users/" not in ia_text_value
        and "timestamp" not in policy_text,
        "clean",
        "determinism",
    )

    # ------------------------------------------------------------- negative A–Z
    scenarios = [
        ("A", "assessment_schema_unchanged", policy.get("schema_change_allowed") is False),
        (
            "B",
            "eir_domain_unchanged",
            'HTML_TEMPLATE_VERSION = "eir-static-html-v2"' in eir_policy_text,
        ),
        ("C", "eir_not_merged_into_assessment", not leaked),
        ("D", "no_commercial_sections_in_community", not docs_leak),
        (
            "E",
            "exec_summary_before_appendix",
            0 <= exec_index < appendix_index,
        ),
        ("F", "single_exec_summary", assessment_html.count('id="executive-summary"') == 1),
        (
            "G",
            "single_h1_per_report",
            _heading_levels(assessment_html).count(1) == 1
            and _heading_levels(eir_html).count(1) == 1,
        ),
        (
            "H",
            "no_heading_skips",
            not _heading_skips(_heading_levels(assessment_html))
            and not _heading_skips(_heading_levels(eir_html)),
        ),
        ("I", "stable_anchors_present", not missing_stable),
        (
            "J",
            "no_duplicate_anchor_ids",
            not [k for k, v in Counter(_ID_RE.findall(assessment_html)).items() if v > 1],
        ),
        (
            "K",
            "toc_targets_exist",
            all(link in assessment_ids for link in assessment_toc)
            and all(link in eir_ids for link in eir_toc),
        ),
        (
            "L",
            "no_broken_internal_links",
            not [
                href
                for href in _HREF_RE.findall(assessment_html)
                if href not in assessment_ids
            ],
        ),
        (
            "M",
            "no_time_based_anchor",
            not [
                sid
                for sid in _SECTION_ID_RE.findall(assessment_html)
                if _TIMESTAMP_RE.search(sid)
            ],
        ),
        (
            "N",
            "finding_evidence_related",
            relationship["cross_reference_required"] is True,
        ),
        (
            "O",
            "recommendation_not_duplicated",
            placement["duplicate_full_content_allowed"] is False
            and len(recommendation_ids) == len(set(recommendation_ids)),
        ),
        ("P", "orientation_before_technical", 0 <= eir_orientation < eir_methodology),
        (
            "Q",
            "no_empty_section_for_nav",
            empty_rules["fabricated_content_to_preserve_nav_allowed"] is False,
        ),
        (
            "R",
            "no_cdn_navigation",
            "http://" not in assessment_html.replace("http://www.w3.org", "")
            and policy.get("navigation_network_dependency_allowed") is False,
        ),
        (
            "S",
            "no_js_navigation",
            "<script" not in assessment_html.lower() and "<script" not in eir_html.lower(),
        ),
        (
            "T",
            "visualization_semantics_unchanged",
            policy.get("visualization_semantics_change_allowed") is False,
        ),
        (
            "U",
            "eir_raw_evidence_not_reintroduced",
            ia["eir"]["evidence_projection"]["raw_evidence_included"] is False
            and 'id="evidence-' not in eir_html,
        ),
        (
            "V",
            "no_content_generation",
            policy.get("content_generation_change_allowed") is False,
        ),
        (
            "W",
            "no_epic_completion_work",
            policy.get("start_slice_15_7") is False,
        ),
        (
            "X",
            "slice_14_14_not_started",
            policy.get("start_slice_15_7") is False
            and all(not (monorepo / rel).exists() for rel in FORBIDDEN_15_7_PATHS),
        ),
        ("Y", "verifier_deterministic", render_eir_html(monorepo) == eir_html),
        (
            "Z",
            "no_leaked_paths_or_time_fields",
            "/Users/" not in policy_text and "timestamp" not in policy_text,
        ),
    ]
    for letter, name, ok in scenarios:
        _add(checks, f"negative:{letter}_{name}", ok, letter, "scenarios")

    meta["assessment_section_count"] = len(assessment_sections)
    meta["eir_section_count"] = len(eir_sections_map)
    return checks, defects, meta
