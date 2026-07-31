"""Parse findings artifacts into normalized intelligence structures."""

from __future__ import annotations

from typing import Any

from codestrata_platform.application.common.errors import PayloadTooLargeError, ValidationError
from codestrata_platform.application.intelligence.parsers._json_utils import (
    load_json_object,
    optional_int,
    optional_string,
    parse_metadata,
    require_string,
)
from codestrata_platform.application.intelligence.parsers.contracts import (
    ParsedAssessmentIntelligence,
    ParsedEvidenceReference,
    ParsedFinding,
)
from codestrata_platform.application.intelligence.parsers.limits import MAX_FINDINGS
from codestrata_platform.domain.artifact.enums import ArtifactType


class FindingsArtifactParser:
    artifact_type = ArtifactType.FINDINGS

    def parse(
        self,
        *,
        schema_version: str,
        content: bytes,
        source_artifact_id: str,
    ) -> ParsedAssessmentIntelligence:
        payload = load_json_object(content)
        raw_findings = payload.get("findings", payload if "rule_id" in payload else [])
        if isinstance(raw_findings, dict):
            raw_findings = raw_findings.get("items", [])
        if not isinstance(raw_findings, list):
            raise ValidationError(
                "Findings artifact must contain a findings list",
                reason_code="invalid_findings_shape",
            )
        if len(raw_findings) > MAX_FINDINGS:
            raise PayloadTooLargeError(
                f"Findings artifact exceeds maximum of {MAX_FINDINGS} findings",
                reason_code="findings_limit_exceeded",
            )
        findings = tuple(
            _parse_finding(item, source_artifact_id=source_artifact_id)
            for item in raw_findings
        )
        return ParsedAssessmentIntelligence(schema_version=schema_version, findings=findings)


def _parse_finding(raw: Any, *, source_artifact_id: str) -> ParsedFinding:
    if not isinstance(raw, dict):
        raise ValidationError(
            "Each finding must be an object",
            reason_code="invalid_finding_shape",
        )
    finding_id = require_string(
        raw.get("finding_id", raw.get("id")),
        field_name="finding_id",
    )
    rule_id = require_string(raw.get("rule_id"), field_name="rule_id")
    title = require_string(raw.get("title"), field_name="title")
    summary = require_string(
        raw.get("summary", raw.get("description")),
        field_name="summary",
    )
    category = require_string(raw.get("category"), field_name="category").lower()
    severity = require_string(raw.get("severity"), field_name="severity").lower()
    confidence_raw = raw.get("confidence", 1.0)
    if isinstance(confidence_raw, bool) or not isinstance(confidence_raw, (int, float)):
        raise ValidationError(
            "Finding confidence must be numeric",
            reason_code="invalid_confidence",
        )
    confidence = float(confidence_raw)
    if confidence < 0 or confidence > 1:
        raise ValidationError(
            "Finding confidence must be between 0 and 1",
            reason_code="invalid_confidence",
        )
    evidence = _parse_evidence_list(
        raw.get("evidence", []),
        source_artifact_id=source_artifact_id,
    )
    return ParsedFinding(
        finding_id=finding_id,
        rule_id=rule_id,
        title=title,
        summary=summary,
        category=category,
        severity=severity,
        confidence=confidence,
        production_scope=optional_string(raw.get("production_scope")),
        affected_component=optional_string(raw.get("affected_component")),
        affected_path_reference=optional_string(
            raw.get("affected_path_reference", raw.get("path"))
        ),
        evidence_references=evidence,
        remediation_reference=optional_string(raw.get("remediation_reference")),
        metadata=parse_metadata(raw.get("metadata")),
    )


def _parse_evidence_list(
    raw: Any,
    *,
    source_artifact_id: str,
) -> tuple[ParsedEvidenceReference, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValidationError(
            "Finding evidence must be a list",
            reason_code="invalid_evidence_shape",
        )
    items: list[ParsedEvidenceReference] = []
    for entry in raw:
        if not isinstance(entry, dict):
            raise ValidationError(
                "Evidence entries must be objects",
                reason_code="invalid_evidence_shape",
            )
        path_reference = require_string(
            entry.get("path_reference", entry.get("file_path", entry.get("path"))),
            field_name="evidence path",
        )
        line_start = optional_int(
            entry.get("line_start", entry.get("line_number")),
            field_name="line_start",
        )
        line_end = optional_int(entry.get("line_end"), field_name="line_end")
        items.append(
            ParsedEvidenceReference(
                path_reference=path_reference,
                line_start=line_start,
                line_end=line_end,
                symbol=optional_string(entry.get("symbol")),
                component=optional_string(entry.get("component")),
                evidence_type=optional_string(entry.get("evidence_type")),
                checksum=optional_string(entry.get("checksum")),
                redacted_excerpt=optional_string(entry.get("redacted_excerpt")),
                source_artifact_id=source_artifact_id,
                evidence_id=optional_string(entry.get("evidence_id")),
            )
        )
    return tuple(items)
