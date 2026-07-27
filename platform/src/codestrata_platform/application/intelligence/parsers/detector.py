"""Detect schema versions from assessment artifact JSON payloads."""

from __future__ import annotations

from codestrata_platform.application.intelligence.parsers._json_utils import load_json_object
from codestrata_platform.domain.artifact.enums import ArtifactType


class DefaultArtifactSchemaDetector:
    """Best-effort schema version detection from artifact JSON."""

    def detect(self, *, artifact_type: ArtifactType, content: bytes) -> str:
        payload = load_json_object(content)
        for key in ("schema_version", "schemaVersion", "version"):
            raw = payload.get(key)
            if isinstance(raw, str) and raw.strip():
                return raw.strip()
            if isinstance(raw, (int, float)) and not isinstance(raw, bool):
                return str(raw)
        if artifact_type is ArtifactType.FINDINGS:
            return "1.0"
        if artifact_type is ArtifactType.EVIDENCE_MANIFEST:
            return "1.0"
        if artifact_type is ArtifactType.ASSESSMENT_SUMMARY:
            return "1.0"
        if artifact_type is ArtifactType.REPORT_JSON:
            return "1.0"
        return "1.0"
