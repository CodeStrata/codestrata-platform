"""Merge parsed intelligence artifacts by source priority."""

from __future__ import annotations

from codestrata_platform.application.intelligence.parsers.contracts import (
    ParsedAssessmentIntelligence,
    ParsedFinding,
    ParsedMetric,
    ParsedRecommendation,
)
from codestrata_platform.domain.artifact.enums import ArtifactType

_ARTIFACT_PRIORITY: dict[ArtifactType, int] = {
    ArtifactType.FINDINGS: 4,
    ArtifactType.EVIDENCE_MANIFEST: 3,
    ArtifactType.ASSESSMENT_SUMMARY: 2,
    ArtifactType.REPORT_JSON: 1,
}


def merge_parsed_intelligence(
    items: tuple[tuple[ArtifactType, ParsedAssessmentIntelligence], ...],
) -> ParsedAssessmentIntelligence:
    ordered = sorted(items, key=lambda item: _ARTIFACT_PRIORITY.get(item[0], 0), reverse=True)
    schema_version = ordered[0][1].schema_version if ordered else "1.0"
    findings = _merge_findings(ordered)
    metrics = _merge_metrics(ordered)
    recommendations = _merge_recommendations(ordered)
    diagnostics = tuple(
        diagnostic
        for _, parsed in ordered
        for diagnostic in parsed.diagnostics
    )
    return ParsedAssessmentIntelligence(
        schema_version=schema_version,
        findings=findings,
        metrics=metrics,
        recommendations=recommendations,
        diagnostics=diagnostics,
    )


def _merge_findings(
    ordered: list[tuple[ArtifactType, ParsedAssessmentIntelligence]],
) -> tuple[ParsedFinding, ...]:
    merged: dict[str, ParsedFinding] = {}
    for _artifact_type, parsed in ordered:
        for finding in parsed.findings:
            merged.setdefault(finding.finding_id, finding)
    return tuple(merged[finding_id] for finding_id in sorted(merged))


def _merge_metrics(
    ordered: list[tuple[ArtifactType, ParsedAssessmentIntelligence]],
) -> tuple[ParsedMetric, ...]:
    merged: dict[str, ParsedMetric] = {}
    for _artifact_type, parsed in ordered:
        for metric in parsed.metrics:
            merged.setdefault(metric.name, metric)
    return tuple(merged[name] for name in sorted(merged))


def _merge_recommendations(
    ordered: list[tuple[ArtifactType, ParsedAssessmentIntelligence]],
) -> tuple[ParsedRecommendation, ...]:
    merged: dict[str, ParsedRecommendation] = {}
    for _artifact_type, parsed in ordered:
        for recommendation in parsed.recommendations:
            merged.setdefault(recommendation.recommendation_id, recommendation)
    return tuple(merged[recommendation_id] for recommendation_id in sorted(merged))
