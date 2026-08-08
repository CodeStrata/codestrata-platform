"""Slice 14.9 IA surface inventory and classification (data only)."""

from __future__ import annotations

ASSESSMENT_SURFACES: dict[str, tuple[str, ...]] = {
    "cover": ("report_identity", "must_preserve"),
    "contents": ("navigation", "safe_to_standardize"),
    "leadership-verdict": ("executive_summary", "must_not_reorder"),
    "executive-summary": ("executive_summary", "must_not_reorder"),
    "engineering-intelligence-summary": ("executive_summary", "must_not_reorder"),
    "key-takeaways": ("executive_summary", "must_not_reorder"),
    "priority-actions": ("recommendation_detail", "must_not_reorder"),
    "engineering-risks": ("executive_summary", "must_not_reorder"),
    "assessment-results": ("primary_analysis", "must_not_reorder"),
    "assessment-head-subsections": ("primary_analysis", "shared_hierarchy"),
    "phased-modernization-plan": ("recommendation_detail", "must_not_reorder"),
    "modernization-advisor": ("supporting_detail", "must_not_reorder"),
    "technical-appendix": ("technical_appendix", "must_not_reorder"),
    "footer": ("report_metadata", "safe_to_standardize"),
    "legacy-pack-aliases": ("deep_link_contract", "legacy_hierarchy", "must_preserve"),
    "finding/recommendation/evidence anchors": ("section_anchor", "deep_link_contract"),
}

EIR_SURFACES: dict[str, tuple[str, ...]] = {
    "cover": ("report_identity", "must_preserve"),
    "toc": ("navigation", "safe_to_standardize"),
    "section-scope": ("orientation", "must_not_reorder"),
    "section-orientation": ("executive_summary", "must_not_reorder"),
    "section-summary": ("executive_summary", "must_not_reorder"),
    "section-technology": ("secondary_analysis", "eir_only"),
    "section-capability": ("primary_analysis", "eir_only"),
    "section-heads": ("primary_analysis", "eir_only"),
    "section-patterns": ("secondary_analysis", "eir_only"),
    "section-observations": ("recommendation_detail", "eir_only"),
    "section-confidence": ("supporting_detail", "shared_hierarchy"),
    "section-limitations": ("limitations", "shared_hierarchy"),
    "section-drilldowns": ("evidence_detail", "eir_only"),
    "section-methodology": ("supporting_detail", "shared_hierarchy"),
    "section-metadata": ("report_metadata", "shared_hierarchy"),
    "footer": ("report_metadata", "safe_to_standardize"),
}

SHARED_LANGUAGE: dict[str, str] = {
    "product_bar": "report_identity",
    "report_title": "report_identity",
    "scope_metadata": "report_metadata",
    "section_header": "shared_hierarchy",
    "section_description": "shared_hierarchy",
    "kpi_metric_placement": "shared_hierarchy",
    "table_placement": "shared_hierarchy",
    "empty_state_placement": "shared_hierarchy",
    "limitations_placement": "limitations",
    "footer": "report_metadata",
}

DEFERRED: dict[str, str] = {
    "universal_assets": "14_10",
    "accessibility_acceptance": "14_11",
    "documentation_deployment": "14_12",
}

__all__ = ["ASSESSMENT_SURFACES", "EIR_SURFACES", "SHARED_LANGUAGE", "DEFERRED"]
