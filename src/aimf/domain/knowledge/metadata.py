"""Source provenance and filterable metadata for knowledge artifacts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aimf.domain.graph.validation import optional_nonblank, require_nonblank
from aimf.domain.knowledge.enums import KnowledgeSourceType


class KnowledgeSource(BaseModel):
    """Provenance pointers for a knowledge document or chunk."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_type: KnowledgeSourceType
    repository_id: str | None = None
    scan_id: str | None = None
    commit_sha: str | None = None
    branch: str | None = None
    file_path: str | None = None
    assessment_type: str | None = None
    finding_id: str | None = None
    rule_id: str | None = None
    evidence_id: str | None = None
    report_section: str | None = None

    @field_validator(
        "repository_id",
        "scan_id",
        "commit_sha",
        "branch",
        "file_path",
        "assessment_type",
        "finding_id",
        "rule_id",
        "evidence_id",
        "report_section",
        mode="before",
    )
    @classmethod
    def normalize_optional(cls, value: object) -> str | None:
        if value is None:
            return None
        return optional_nonblank(str(value), label="knowledge source field")


class KnowledgeMetadata(BaseModel):
    """Filterable facets attached to documents, chunks, and vector records."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str | None = None
    repository_id: str | None = None
    scan_id: str | None = None
    branch: str | None = None
    commit_sha: str | None = None
    language: str | None = None
    framework: str | None = None
    source_type: KnowledgeSourceType | None = None
    intelligence_pack: str | None = None
    assessment_version: str | None = None
    finding_id: str | None = None
    rule_id: str | None = None
    severity: str | None = None
    confidence: str | None = None
    file_path: str | None = None
    symbol_name: str | None = None
    content_hash: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    @field_validator(
        "tenant_id",
        "repository_id",
        "scan_id",
        "branch",
        "commit_sha",
        "language",
        "framework",
        "intelligence_pack",
        "assessment_version",
        "finding_id",
        "rule_id",
        "severity",
        "confidence",
        "file_path",
        "symbol_name",
        "content_hash",
        mode="before",
    )
    @classmethod
    def normalize_optional(cls, value: object) -> str | None:
        if value is None:
            return None
        return optional_nonblank(str(value), label="knowledge metadata field")

    @field_validator("extra", mode="before")
    @classmethod
    def normalize_extra(cls, value: object) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, Mapping):
            raise ValueError("extra must be a mapping")
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("extra keys must be strings")
            compact = key.strip()
            if not compact:
                raise ValueError("extra keys must not be blank")
            cleaned[compact] = item
        return cleaned

    def as_filter_dict(self) -> dict[str, Any]:
        """Return a flat JSON dict suitable for vector metadata filtering.

        ``None`` fields are omitted. ``extra`` keys are merged last and must not
        collide with reserved facet names.
        """

        reserved = {
            "tenant_id",
            "repository_id",
            "scan_id",
            "branch",
            "commit_sha",
            "language",
            "framework",
            "source_type",
            "intelligence_pack",
            "assessment_version",
            "finding_id",
            "rule_id",
            "severity",
            "confidence",
            "file_path",
            "symbol_name",
            "content_hash",
        }
        payload = self.model_dump(mode="json", exclude_none=True, exclude={"extra"})
        for key in self.extra:
            if key in reserved:
                raise ValueError(f"extra key collides with reserved metadata field: {key}")
        merged = dict(payload)
        merged.update(self.extra)
        return merged


class KnowledgeTraceability(BaseModel):
    """Audit lineage binding a knowledge artifact to its upstream source."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source: KnowledgeSource
    source_id: str
    assessment_version: str | None = None
    parent_document_id: str | None = None
    notes: str | None = None

    @field_validator("source_id", mode="before")
    @classmethod
    def normalize_source_id(cls, value: object) -> str:
        return require_nonblank(str(value), label="source_id")

    @field_validator("assessment_version", "parent_document_id", "notes", mode="before")
    @classmethod
    def normalize_optional(cls, value: object) -> str | None:
        if value is None:
            return None
        return optional_nonblank(str(value), label="traceability field")
