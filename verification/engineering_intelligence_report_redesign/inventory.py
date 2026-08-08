"""Surface inventory classification for Slice 14.4."""

from __future__ import annotations

SURFACE_CLASSIFICATION: dict[str, str] = {
    "eir_domain_report": "intelligence_truth",
    "website_safe_projection": "intelligence_truth",
    "static_html_renderer": "report_presentation",
    "static_html_styles": "design_system_consumer",
    "executive_orientation": "executive_summary",
    "assessment_head_distributions": "intelligence_metric",
    "architecture_as_head": "architecture",
    "dependency_as_head": "dependency",
    "technical_debt_as_head": "technical_debt",
    "security_as_head": "security",
    "cloud_as_head": "cloud",
    "ai_readiness_as_head": "ai",
    "modernization_observations": "modernization",
    "drilldown_findings": "finding",
    "evidence_omit_policy": "must_not_change",
    "drilldown_recommendations": "recommendation",
    "ingestion_traceability": "traceability",
    "confidence_level": "score",
    "severity_labels": "risk",
    "no_charts_present": "deferred_to_14_8_visualization",
    "tables": "table",
    "toc_navigation": "navigation",
    "responsive_css": "responsive",
    "print_css": "print",
    "accessibility_landmarks": "accessibility",
    "legacy_georgia_palette": "legacy_visual_style",
    "cross_report_ia": "deferred_to_14_9_information_hierarchy",
    "platform_commercial_boundary": "commercial_or_internal_content",
    "assessment_schema_1_2": "must_not_change",
    "eir_aggregation_logic": "must_not_change",
}


def inventory_summary() -> dict[str, int]:
    counts: dict[str, int] = {}
    for label in SURFACE_CLASSIFICATION.values():
        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items()))
