"""Orchestrate parsing of completed assessment artifacts."""

from __future__ import annotations

from codestrata_platform.application.common.errors import ValidationError
from codestrata_platform.application.intelligence.parsers.contracts import (
    ParsedAssessmentIntelligence,
)
from codestrata_platform.application.intelligence.parsers.evidence_manifest_parser import (
    EvidenceManifestParser,
)
from codestrata_platform.application.intelligence.parsers.findings_parser import (
    FindingsArtifactParser,
)
from codestrata_platform.application.intelligence.parsers.merge import merge_parsed_intelligence
from codestrata_platform.application.intelligence.parsers.report_json_parser import ReportJsonParser
from codestrata_platform.application.intelligence.parsers.summary_parser import (
    AssessmentSummaryParser,
)
from codestrata_platform.domain.artifact.enums import ArtifactType

_SUPPORTED_TYPES = frozenset(
    {
        ArtifactType.FINDINGS,
        ArtifactType.EVIDENCE_MANIFEST,
        ArtifactType.ASSESSMENT_SUMMARY,
        ArtifactType.REPORT_JSON,
    }
)

_PARSERS = {
    ArtifactType.FINDINGS: FindingsArtifactParser(),
    ArtifactType.EVIDENCE_MANIFEST: EvidenceManifestParser(),
    ArtifactType.ASSESSMENT_SUMMARY: AssessmentSummaryParser(),
    ArtifactType.REPORT_JSON: ReportJsonParser(),
}


def parse_artifacts(
    artifacts: list[tuple[ArtifactType, str, bytes, str]],
) -> ParsedAssessmentIntelligence:
    """Parse artifact tuples of (type, schema_version, content, artifact_id)."""

    if not artifacts:
        raise ValidationError(
            "At least one artifact is required for parsing",
            reason_code="empty_artifact_set",
        )
    parsed_items: list[tuple[ArtifactType, ParsedAssessmentIntelligence]] = []
    for artifact_type, schema_version, content, artifact_id in artifacts:
        if artifact_type not in _SUPPORTED_TYPES:
            if artifact_type is ArtifactType.REPORT_HTML:
                continue
            raise ValidationError(
                f"Unsupported artifact type for intelligence parsing: {artifact_type.value}",
                reason_code="unsupported_artifact_type",
            )
        parser = _PARSERS[artifact_type]
        parsed_items.append(
            (
                artifact_type,
                parser.parse(
                    schema_version=schema_version,
                    content=content,
                    source_artifact_id=artifact_id,
                ),
            )
        )
    return merge_parsed_intelligence(tuple(parsed_items))
