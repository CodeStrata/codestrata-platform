"""Parse evidence manifest artifacts."""

from __future__ import annotations

from typing import Any

from codestrata_platform.application.common.errors import PayloadTooLargeError, ValidationError
from codestrata_platform.application.intelligence.parsers._json_utils import (
    load_json_object,
    optional_int,
    optional_string,
    require_string,
)
from codestrata_platform.application.intelligence.parsers.contracts import (
    ParsedAssessmentIntelligence,
    ParsedEvidenceReference,
    ParsedFinding,
)
from codestrata_platform.application.intelligence.parsers.limits import MAX_FINDINGS
from codestrata_platform.domain.artifact.enums import ArtifactType


class EvidenceManifestParser:
    artifact_type = ArtifactType.EVIDENCE_MANIFEST

    def parse(
        self,
        *,
        schema_version: str,
        content: bytes,
        source_artifact_id: str,
    ) -> ParsedAssessmentIntelligence:
        payload = load_json_object(content)
        raw_evidence = payload.get("evidence", [])
        if not isinstance(raw_evidence, list):
            raise ValidationError(
                "Evidence manifest must contain an evidence list",
                reason_code="invalid_evidence_manifest",
            )
        if len(raw_evidence) > MAX_FINDINGS:
            raise PayloadTooLargeError(
                f"Evidence manifest exceeds maximum of {MAX_FINDINGS} entries",
                reason_code="findings_limit_exceeded",
            )
        grouped: dict[str, list[ParsedEvidenceReference]] = {}
        for entry in raw_evidence:
            evidence = _parse_evidence(entry, source_artifact_id=source_artifact_id)
            grouped.setdefault(evidence.path_reference, []).append(evidence)
        findings = tuple(
            ParsedFinding(
                finding_id=f"evidence:{path_reference}",
                rule_id="evidence.manifest",
                title=f"Evidence at {path_reference}",
                summary=f"Evidence manifest entry for {path_reference}",
                category="other",
                severity="info",
                confidence=1.0,
                affected_path_reference=path_reference,
                evidence_references=tuple(items),
            )
            for path_reference, items in sorted(grouped.items())
        )
        return ParsedAssessmentIntelligence(schema_version=schema_version, findings=findings)


def _parse_evidence(raw: Any, *, source_artifact_id: str) -> ParsedEvidenceReference:
    if not isinstance(raw, dict):
        raise ValidationError(
            "Evidence entries must be objects",
            reason_code="invalid_evidence_shape",
        )
    path_reference = require_string(
        raw.get("path_reference", raw.get("file_path", raw.get("path"))),
        field_name="evidence path",
    )
    return ParsedEvidenceReference(
        path_reference=path_reference,
        line_start=optional_int(raw.get("line_start"), field_name="line_start"),
        line_end=optional_int(raw.get("line_end"), field_name="line_end"),
        symbol=optional_string(raw.get("symbol")),
        component=optional_string(raw.get("component")),
        evidence_type=optional_string(raw.get("evidence_type")),
        checksum=optional_string(raw.get("checksum")),
        redacted_excerpt=optional_string(raw.get("redacted_excerpt")),
        source_artifact_id=source_artifact_id,
    )
