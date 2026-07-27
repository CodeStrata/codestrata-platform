"""Parse assessment summary artifacts."""

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
    ParsedMetric,
)
from codestrata_platform.application.intelligence.parsers.limits import MAX_METRICS
from codestrata_platform.domain.artifact.enums import ArtifactType


class AssessmentSummaryParser:
    artifact_type = ArtifactType.ASSESSMENT_SUMMARY

    def parse(
        self,
        *,
        schema_version: str,
        content: bytes,
        source_artifact_id: str,
    ) -> ParsedAssessmentIntelligence:
        del source_artifact_id
        payload = load_json_object(content)
        metrics = _parse_metrics(payload)
        return ParsedAssessmentIntelligence(schema_version=schema_version, metrics=metrics)


def _parse_metrics(payload: dict[str, Any]) -> tuple[ParsedMetric, ...]:
    metrics: list[ParsedMetric] = []
    raw_metrics = payload.get("metrics")
    if isinstance(raw_metrics, dict):
        for name, value in raw_metrics.items():
            metrics.extend(_metric_from_name_value(name, value))
    raw_scores = payload.get("scores")
    if isinstance(raw_scores, dict):
        for name, value in raw_scores.items():
            metrics.extend(_metric_from_name_value(f"assessment.scores.{name}", value))
    counts = payload.get("counts")
    if isinstance(counts, dict):
        for name, value in counts.items():
            metrics.extend(_metric_from_name_value(f"assessment.counts.{name}", value))
    if len(metrics) > MAX_METRICS:
        raise PayloadTooLargeError(
            f"Summary metrics exceed maximum of {MAX_METRICS}",
            reason_code="metrics_limit_exceeded",
        )
    return tuple(metrics)


def _metric_from_name_value(name: str, value: Any) -> list[ParsedMetric]:
    metric_name = require_string(name, field_name="metric name").lower()
    if not metric_name.startswith("assessment."):
        metric_name = f"assessment.{metric_name}"
    if isinstance(value, bool):
        raise ValidationError(
            "Metric values must not be boolean",
            reason_code="invalid_metric_value",
        )
    if isinstance(value, int):
        return [
            ParsedMetric(
                name=metric_name,
                kind="integer",
                value=str(value),
            )
        ]
    if isinstance(value, float):
        kind = "percentage" if metric_name.endswith(".percentage") else "decimal"
        return [
            ParsedMetric(
                name=metric_name,
                kind=kind,
                value=str(value),
            )
        ]
    if isinstance(value, str):
        compact = require_string(value, field_name="metric value")
        return [
            ParsedMetric(
                name=metric_name,
                kind="text",
                value=compact,
            )
        ]
    if isinstance(value, dict):
        kind = optional_string(value.get("kind")) or "text"
        raw_value = value.get("value")
        if raw_value is None:
            raise ValidationError(
                "Metric object must include value",
                reason_code="invalid_metric_value",
            )
        return [
            ParsedMetric(
                name=metric_name,
                kind=kind.lower(),
                value=require_string(raw_value, field_name="metric value"),
                unit=optional_string(value.get("unit")),
                metadata=parse_metadata(value.get("metadata")),
            )
        ]
    raise ValidationError(
        "Unsupported metric value type",
        reason_code="invalid_metric_value",
    )
