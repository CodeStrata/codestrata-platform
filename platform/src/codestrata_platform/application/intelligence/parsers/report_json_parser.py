"""Parse report_json artifacts.

Epic 2 Slice 2.8: preserve the canonical Engine ``report.json`` document and
schema 1.2 additive traceability collections. Decomposed findings/recommendations
are projections only — relationships are not regenerated.
"""

from __future__ import annotations

import copy
import json
from typing import Any

from codestrata.reporting.traceability.preservation import (
    CanonicalReportLoadError,
    classify_traceability_state,
    extract_assessment,
    schema_version_of,
    validate_canonical_assessment,
)

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
    MAX_METRICS,
    MAX_RECOMMENDATIONS,
)
from codestrata_platform.application.intelligence.parsers.summary_parser import _parse_metrics
from codestrata_platform.domain.artifact.enums import ArtifactType

# Compact metadata keys for Entity projections (full chain lives on canonical_report).
_META_PRIMARY_EVIDENCE = "cs.trace.primary_evidence_id"
_META_EVIDENCE_COMPLETENESS = "cs.trace.evidence_completeness"
_META_LIMITATIONS = "cs.trace.limitations"
_META_SYNTHESIZED = "cs.trace.synthesized_from_evidence_ids"
_META_SUPPORTING_FINDINGS = "cs.trace.supporting_finding_ids"
_META_PRIMARY_FINDING = "cs.trace.primary_finding_id"
_META_REC_TYPE = "cs.trace.recommendation_type"


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
        canonical = copy.deepcopy(payload)
        try:
            assessment = extract_assessment(payload)
        except CanonicalReportLoadError:
            # Flat legacy Platform test payloads without assessment envelope.
            assessment = payload if isinstance(payload, dict) else {}

        reported_schema = schema_version_of(payload)
        if reported_schema and reported_schema != schema_version:
            # Prefer document schema when present; keep artifact schema as fallback.
            effective_schema = reported_schema
        else:
            effective_schema = schema_version

        findings = _parse_findings(assessment, payload, source_artifact_id=source_artifact_id)
        recommendations = _parse_recommendations(assessment, payload)
        metrics = list(_parse_metrics(payload))

        evidence_raw = assessment.get("evidence")
        evidence = tuple(
            copy.deepcopy(item)
            for item in (evidence_raw if isinstance(evidence_raw, list) else [])
            if isinstance(item, dict)
        )
        pas_raw = assessment.get("priority_actions")
        priority_actions = tuple(
            copy.deepcopy(item)
            for item in (pas_raw if isinstance(pas_raw, list) else [])
            if isinstance(item, dict)
        )
        roadmap_raw = assessment.get("roadmap")
        assessment_roadmap = (
            copy.deepcopy(roadmap_raw) if isinstance(roadmap_raw, dict) else None
        )

        status = classify_traceability_state(assessment)
        try:
            status = validate_canonical_assessment(assessment)
        except CanonicalReportLoadError as error:
            raise ValidationError(
                f"Canonical report traceability validation failed: {error}",
                reason_code="traceability_validation_failed",
            ) from error

        if len(metrics) > MAX_METRICS:
            raise PayloadTooLargeError(
                f"Report metrics exceed maximum of {MAX_METRICS}",
                reason_code="metrics_limit_exceeded",
            )

        diagnostics = (
            f"traceability_status:{status}",
            "canonical_interchange:assessment_report_json",
            "assessment_roadmap:repository_scoped_not_platform_strategic",
        )
        return ParsedAssessmentIntelligence(
            schema_version=effective_schema,
            findings=findings,
            metrics=tuple(metrics),
            recommendations=recommendations,
            diagnostics=diagnostics,
            canonical_report=canonical,
            assessment_evidence=evidence,
            priority_actions=priority_actions,
            assessment_roadmap=assessment_roadmap,
            traceability_status=status,
        )


def _parse_findings(
    assessment: dict[str, Any],
    payload: dict[str, Any],
    *,
    source_artifact_id: str,
) -> tuple[Any, ...]:
    raw_findings = assessment.get("findings", payload.get("findings", []))
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
        _enrich_finding_traceability(
            _parse_finding(item, source_artifact_id=source_artifact_id),
            raw=item if isinstance(item, dict) else {},
            source_artifact_id=source_artifact_id,
        )
        for item in raw_findings
    )


def _enrich_finding_traceability(
    parsed: Any,
    *,
    raw: dict[str, Any],
    source_artifact_id: str,
) -> Any:
    """Attach Epic 2 Finding fields without fabricating missing values."""

    from codestrata_platform.application.intelligence.parsers.contracts import ParsedFinding

    assert isinstance(parsed, ParsedFinding)
    primary = optional_string(raw.get("primary_evidence_id"))
    completeness = optional_string(raw.get("evidence_completeness"))
    limitations = _string_tuple(raw.get("limitations") or [])
    synthesized = _string_tuple(raw.get("synthesized_from_evidence_ids") or [])
    metadata = dict(parsed.metadata)
    if primary:
        metadata.setdefault(_META_PRIMARY_EVIDENCE, primary)
    if completeness:
        metadata.setdefault(_META_EVIDENCE_COMPLETENESS, completeness)
    if limitations:
        metadata.setdefault(_META_LIMITATIONS, json.dumps(list(limitations)))
    if synthesized:
        metadata.setdefault(_META_SYNTHESIZED, json.dumps(list(synthesized)))

    # Prefer EvidenceRef envelopes for projection when thin evidence is empty.
    evidence = parsed.evidence_references
    evidence_refs = raw.get("evidence_refs")
    if not evidence and isinstance(evidence_refs, list):
        evidence = _evidence_from_refs(
            evidence_refs,
            source_artifact_id=source_artifact_id,
        )

    return ParsedFinding(
        finding_id=parsed.finding_id,
        rule_id=parsed.rule_id,
        title=parsed.title,
        summary=parsed.summary,
        category=parsed.category,
        severity=parsed.severity,
        confidence=parsed.confidence,
        production_scope=parsed.production_scope,
        affected_component=parsed.affected_component,
        affected_path_reference=parsed.affected_path_reference,
        evidence_references=evidence,
        remediation_reference=parsed.remediation_reference,
        metadata=metadata,
        primary_evidence_id=primary,
        synthesized_from_evidence_ids=synthesized,
        evidence_completeness=completeness,
        limitations=limitations,
    )


def _evidence_from_refs(
    refs: list[Any],
    *,
    source_artifact_id: str | None,
) -> tuple[Any, ...]:
    from codestrata_platform.application.intelligence.parsers.contracts import (
        ParsedEvidenceReference,
    )

    items: list[ParsedEvidenceReference] = []
    for entry in refs:
        if not isinstance(entry, dict):
            continue
        evidence_id = optional_string(entry.get("evidence_id"))
        location = entry.get("location") if isinstance(entry.get("location"), dict) else {}
        path = optional_string(
            location.get("path")
            or location.get("relative_path")
            or entry.get("path_reference")
            or entry.get("path")
        )
        if path is None:
            # Safe placeholder — do not invent repository paths.
            path = "evidence://unlocated"
        snippet = entry.get("snippet") if isinstance(entry.get("snippet"), dict) else {}
        excerpt = optional_string(
            snippet.get("text") or snippet.get("redacted_text") or entry.get("redacted_excerpt")
        )
        items.append(
            ParsedEvidenceReference(
                path_reference=path,
                line_start=_optional_line(location.get("start_line") or location.get("line_start")),
                line_end=_optional_line(location.get("end_line") or location.get("line_end")),
                symbol=optional_string(location.get("symbol") or entry.get("symbol")),
                component=optional_string(entry.get("component")),
                evidence_type=optional_string(
                    entry.get("kind") or entry.get("evidence_type")
                ),
                checksum=optional_string(entry.get("checksum")),
                redacted_excerpt=excerpt,
                source_artifact_id=source_artifact_id
                or optional_string(entry.get("source_artifact")),
                evidence_id=evidence_id,
            )
        )
    return tuple(items)


def _optional_line(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 1 else None
    if isinstance(value, float) and value.is_integer():
        ivalue = int(value)
        return ivalue if ivalue >= 1 else None
    return None


def _parse_recommendations(
    assessment: dict[str, Any],
    payload: dict[str, Any],
) -> tuple[ParsedRecommendation, ...]:
    raw_recommendations = assessment.get(
        "deterministic_recommendations",
        payload.get("recommendations", payload.get("deterministic_recommendations", [])),
    )
    if raw_recommendations is None:
        raw_recommendations = []
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
            raw.get("rationale", raw.get("description", raw.get("summary"))),
            field_name="rationale",
        )
        priority = require_string(raw.get("priority"), field_name="priority").lower()
        category = require_string(raw.get("category"), field_name="category").lower()
        supporting = _string_tuple(
            raw.get("supporting_finding_ids") or raw.get("related_finding_ids") or []
        )
        related = _string_tuple(
            raw.get("related_finding_ids") or raw.get("supporting_finding_ids") or []
        )
        dependencies = _string_tuple(raw.get("dependencies") or [])
        primary_finding = optional_string(raw.get("primary_finding_id"))
        rec_type = optional_string(raw.get("recommendation_type"))
        completeness = optional_string(raw.get("evidence_completeness"))
        limitations = _string_tuple(raw.get("limitations"))
        metadata = parse_metadata(raw.get("metadata"))
        if supporting:
            metadata.setdefault(_META_SUPPORTING_FINDINGS, json.dumps(list(supporting)))
        if primary_finding:
            metadata.setdefault(_META_PRIMARY_FINDING, primary_finding)
        if rec_type:
            metadata.setdefault(_META_REC_TYPE, rec_type)
        if completeness:
            metadata.setdefault(_META_EVIDENCE_COMPLETENESS, completeness)
        if limitations:
            metadata.setdefault(_META_LIMITATIONS, json.dumps(list(limitations)))
        items.append(
            ParsedRecommendation(
                recommendation_id=recommendation_id,
                title=title,
                rationale=rationale,
                priority=priority,
                category=category,
                effort=optional_string(raw.get("effort")),
                impact=optional_string(raw.get("impact")),
                dependencies=dependencies,
                related_finding_ids=related,
                roadmap_horizon=optional_string(
                    raw.get("roadmap_horizon") or raw.get("roadmap_phase")
                ),
                metadata=metadata,
                supporting_finding_ids=supporting,
                primary_finding_id=primary_finding,
                recommendation_type=rec_type,
                evidence_completeness=completeness,
                limitations=limitations,
            )
        )
    return tuple(items)


def _string_tuple(raw: Any) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValidationError(
            "Expected a string list",
            reason_code="invalid_string_list",
        )
    if not all(isinstance(item, str) for item in raw):
        raise ValidationError(
            "Expected a string list",
            reason_code="invalid_string_list",
        )
    return tuple(item.strip() for item in raw if item.strip())
