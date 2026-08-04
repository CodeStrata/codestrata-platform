"""Markdown + JSON reporting helpers for SV.12."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.engineering_intelligence_quality.models import QualityReviewReport


def write_review_markdown(report: QualityReviewReport, path: Path) -> None:
    lines = [
        "# Engineering Intelligence Quality Review (SV.12)",
        "",
        f"**Verdict:** {report.verdict}",
        f"**Repositories:** {report.repository_count}",
        f"**Dataset ID:** {report.dataset_id}",
        f"**EIR Report ID:** {report.eir_report_id}",
        f"**Interpretation policy bundle:** {report.interpretation_policy_bundle_id}",
        f"**Website export ID:** {report.website_export_id}",
        "",
        "## Summary",
        "",
        f"- Defect candidates: {len(report.defect_candidates)}",
        f"- Editorial observations: {len(report.editorial_observations)}",
        "",
        "## Commercial usefulness",
        "",
    ]
    for row in report.commercial_usefulness:
        lines.append(f"- **{row.get('audience')}**: {row.get('classification')}")
        for note in row.get("notes") or []:
            lines.append(f"  - {note}")
    lines.extend(["", "## Section reviews", ""])
    for key in (
        "dataset_review",
        "technology_distribution_review",
        "capability_comparison_review",
        "assessment_head_review",
        "recurring_pattern_review",
        "modernization_observation_review",
        "confidence_review",
        "limitation_review",
        "repository_drilldown_review",
        "provenance_review",
        "wording_review",
        "usability_review",
        "website_safe_review",
        "special_case_review",
        "signal_to_noise",
    ):
        section = getattr(report, key, {}) or {}
        if isinstance(section, dict):
            lines.append(
                f"- **{key}**: ok={section.get('ok')} — {section.get('summary', '')}"
            )
    lines.extend(["", "## Limitations", ""])
    for item in report.limitations:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Disclaimer",
            "",
            "Results apply only to the 22 curated pinned repositories in the v0.2.0 "
            "release-validation catalog. This is not an industry benchmark or "
            "product-wide accuracy claim.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def signal_to_noise_summary(payload: dict[str, Any], *, json_bytes: int, html_bytes: int) -> dict[str, Any]:
    tech = payload.get("technology_distribution") or {}
    tech_n = len(tech.get("observations") or tech.get("items") or []) if isinstance(tech, dict) else 0
    patterns_n = len(payload.get("recurring_patterns") or [])
    mods_n = len(payload.get("modernization_observations") or [])
    lim_n = len(payload.get("limitations") or [])
    drills_n = len(payload.get("repository_drilldowns") or [])
    caps_n = len(payload.get("capability_comparisons") or [])
    heads_n = len(payload.get("assessment_head_distributions") or [])
    classification = "balanced"
    if patterns_n > 100 or tech_n > 100:
        classification = "noisy"
    elif patterns_n == 0 and mods_n == 0:
        classification = "sparse"
    return {
        "ok": True,
        "classification": classification,
        "counts": {
            "technology_observations": tech_n,
            "capability_comparisons": caps_n,
            "assessment_head_distributions": heads_n,
            "recurring_patterns": patterns_n,
            "modernization_observations": mods_n,
            "limitations": lim_n,
            "repository_drilldowns": drills_n,
            "json_bytes": json_bytes,
            "html_bytes": html_bytes,
        },
        "summary": f"Signal-to-noise qualitatively {classification}",
    }
