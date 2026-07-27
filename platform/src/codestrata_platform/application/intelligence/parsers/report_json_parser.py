"""Parse report_json artifacts."""

from __future__ import annotations

from typing import Any

from codestrata_platform.application.common.errors import PayloadTooLargeError, ValidationError
from codestrata_platform.application.intelligence.parsers._json_utils import (
    load_json_object,
    optional_string,
    parse_metadata,
    require_string,
)
from codestrata_platform.application.intelligence.parsers.contracts import (
    ParsedAssessmentIntelligence,
    ParsedRecommendation,
)
from codestrata_platform.application.intelligence.parsers.findings_parser import _parse_finding
from codestrata_platform.application.intelligence.parsers.limits import (
    MAX_FINDINGS,
    MAX_RECOMMENDATIONS,
)
from codestrata_platform.application.intelligence.parsers.summary_parser import _parse_metrics
from codestrata_platform.domain.artifact.enums import ArtifactType


class ReportJsonParser:
    artifact_type = ArtifactType.REPORT_JSON

    def parse(
        self,
        *,
        schema_version: str,
        content: bytes,
        source_artifact_id: str,
    ) -> ParsedAssessmentIntelligence:
        payload = load_json_object(content)
        findings = _parse_findings(payload, source_artifact_id=source_artifact_id)
        recommendations = _parse_recommendations(payload)
        metrics = _parse_metrics(payload)
        return ParsedAssessmentIntelligence(
            schema_version=schema_version,
            findings=findings,
            metrics=metrics,
            recommendations=recommendations,
        )


def _parse_findings(payload: dict[str, Any], *, source_artifact_id: str) -> tuple[Any, ...]:
    raw_findings = payload.get("findings", [])
    if not isinstance(raw_findings, list):
        raise ValidationError(
            "Report findings must be a list",
            reason_code="invalid_findings_shape",
        )
    if len(raw_findings) > MAX_FINDINGS:
        raise PayloadTooLargeError(
            f"Report findings exceed maximum of {MAX_FINDINGS}",
            reason_code="findings_limit_exceeded",
        )
    return tuple(
        _parse_finding(item, source_artifact_id=source_artifact_id)
        for item in raw_findings
    )


def _parse_recommendations(payload: dict[str, Any]) -> tuple[ParsedRecommendation, ...]:
    raw_recommendations = payload.get("recommendations", [])
    if not isinstance(raw_recommendations, list):
        raise ValidationError(
            "Report recommendations must be a list",
            reason_code="invalid_recommendations_shape",
        )
    if len(raw_recommendations) > MAX_RECOMMENDATIONS:
        raise PayloadTooLargeError(
            f"Report recommendations exceed maximum of {MAX_RECOMMENDATIONS}",
            reason_code="recommendations_limit_exceeded",
        )
    items: list[ParsedRecommendation] = []
    for raw in raw_recommendations:
        if not isinstance(raw, dict):
            raise ValidationError(
                "Each recommendation must be an object",
                reason_code="invalid_recommendation_shape",
            )
        recommendation_id = require_string(
            raw.get("recommendation_id", raw.get("id")),
            field_name="recommendation_id",
        )
        title = require_string(raw.get("title"), field_name="title")
        rationale = require_string(
            raw.get("rationale", raw.get("description")),
            field_name="rationale",
        )
        priority = require_string(raw.get("priority"), field_name="priority").lower()
        category = require_string(raw.get("category"), field_name="category").lower()
        related = raw.get("related_finding_ids", [])
        dependencies = raw.get("dependencies", [])
        if not isinstance(related, list) or not all(isinstance(item, str) for item in related):
            raise ValidationError(
                "related_finding_ids must be a string list",
                reason_code="invalid_related_findings",
            )
        if not isinstance(dependencies, list) or not all(
            isinstance(item, str) for item in dependencies
        ):
            raise ValidationError(
                "dependencies must be a string list",
                reason_code="invalid_dependencies",
            )
        items.append(
            ParsedRecommendation(
                recommendation_id=recommendation_id,
                title=title,
                rationale=rationale,
                priority=priority,
                category=category,
                effort=optional_string(raw.get("effort")),
                impact=optional_string(raw.get("impact")),
                dependencies=tuple(item.strip() for item in dependencies if item.strip()),
                related_finding_ids=tuple(item.strip() for item in related if item.strip()),
                roadmap_horizon=optional_string(raw.get("roadmap_horizon")),
                metadata=parse_metadata(raw.get("metadata")),
            )
        )
    return tuple(items)
