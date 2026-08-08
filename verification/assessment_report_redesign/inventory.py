"""Surface inventory classification for Slice 14.3 (documentation aid)."""

from __future__ import annotations

# Classification labels (not executable product logic).
SURFACE_CLASSIFICATION: dict[str, str] = {
    "report_html_renderer": "report_presentation",
    "html_v2_styles": "design_system_consumer",
    "design_system_tokens_embed": "design_system_consumer",
    "report_json": "assessment_truth",
    "assessment_schema_1_2": "must_not_change",
    "executive_summary_section": "executive_summary",
    "assessment_heads": "assessment_head",
    "findings": "finding",
    "evidence": "evidence",
    "recommendations": "recommendation",
    "scores_presentation": "score",
    "severity_badges": "risk",
    "section_navigation": "navigation",
    "print_css": "print",
    "responsive_css": "responsive",
    "accessibility_landmarks": "accessibility",
    "charts_existing": "deferred_to_14_8_visualization",
    "cross_report_ia": "deferred_to_14_9_information_hierarchy",
    "platform_eir": "engineering_intelligence_only",
    "legacy_amber_palette": "legacy_visual_style",
    "scoring_algorithms": "must_not_change",
    "analyzers_rules": "must_not_change",
}


def inventory_summary() -> dict[str, int]:
    counts: dict[str, int] = {}
    for label in SURFACE_CLASSIFICATION.values():
        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items()))
