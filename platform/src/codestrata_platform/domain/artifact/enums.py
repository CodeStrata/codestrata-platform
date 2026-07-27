"""Artifact enums."""

from __future__ import annotations

from enum import StrEnum


class ArtifactType(StrEnum):
    ASSESSMENT_SUMMARY = "assessment_summary"
    REPORT_JSON = "report_json"
    REPORT_HTML = "report_html"
    FINDINGS = "findings"
    EVIDENCE_MANIFEST = "evidence_manifest"
    KNOWLEDGE_EXPORT = "knowledge_export"


class ArtifactFormat(StrEnum):
    JSON = "json"
    HTML = "html"
    TEXT = "text"
    BINARY = "binary"


class ArtifactStatus(StrEnum):
    REGISTERED = "registered"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"
