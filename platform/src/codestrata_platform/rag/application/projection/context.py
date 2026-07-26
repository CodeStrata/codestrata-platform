"""Projection context and shared helpers (Phase 5.2)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from codestrata.domain.findings.models import Finding
from codestrata.domain.recommendations.models import Recommendation
from codestrata.domain.repository.manifests import RepositoryManifest
from codestrata.services.inventory.content_reader import RepositoryContentReader
from codestrata_platform.rag.domain.corpus import KnowledgeDiagnostic
from codestrata_platform.rag.domain.enums import KnowledgeSourceType
from codestrata_platform.rag.domain.metadata import (
    KnowledgeMetadata,
    KnowledgeSource,
    KnowledgeTraceability,
)
from codestrata_platform.rag.domain.models import KnowledgeDocument


@dataclass(frozen=True, slots=True)
class ProjectionContext:
    """Isolation and revision context shared by all projectors."""

    tenant_id: str | None
    repository_id: str
    scan_id: str
    branch: str | None = None
    commit_sha: str | None = None
    assessment_version: str | None = None

    def base_metadata(
        self,
        *,
        source_type: KnowledgeSourceType,
        intelligence_pack: str | None = None,
        finding_id: str | None = None,
        rule_id: str | None = None,
        severity: str | None = None,
        confidence: str | None = None,
        file_path: str | None = None,
        symbol_name: str | None = None,
        content_hash: str | None = None,
        language: str | None = None,
        framework: str | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> KnowledgeMetadata:
        return KnowledgeMetadata(
            tenant_id=self.tenant_id,
            repository_id=self.repository_id,
            scan_id=self.scan_id,
            branch=self.branch,
            commit_sha=self.commit_sha,
            language=language,
            framework=framework,
            source_type=source_type,
            intelligence_pack=intelligence_pack,
            assessment_version=self.assessment_version,
            finding_id=finding_id,
            rule_id=rule_id,
            severity=severity,
            confidence=confidence,
            file_path=file_path,
            symbol_name=symbol_name,
            content_hash=content_hash,
            extra=dict(extra or {}),
        )

    def traceability(
        self,
        *,
        source_type: KnowledgeSourceType,
        source_id: str,
        file_path: str | None = None,
        assessment_type: str | None = None,
        finding_id: str | None = None,
        rule_id: str | None = None,
        evidence_id: str | None = None,
        report_section: str | None = None,
        notes: str | None = None,
        parent_document_id: str | None = None,
    ) -> KnowledgeTraceability:
        return KnowledgeTraceability(
            source=KnowledgeSource(
                source_type=source_type,
                repository_id=self.repository_id,
                scan_id=self.scan_id,
                commit_sha=self.commit_sha,
                branch=self.branch,
                file_path=file_path,
                assessment_type=assessment_type,
                finding_id=finding_id,
                rule_id=rule_id,
                evidence_id=evidence_id,
                report_section=report_section,
            ),
            source_id=source_id,
            assessment_version=self.assessment_version,
            parent_document_id=parent_document_id,
            notes=notes,
        )


@dataclass
class ProjectorResult:
    """Documents and diagnostics produced by one projector."""

    documents: list[KnowledgeDocument] = field(default_factory=list)
    diagnostics: list[KnowledgeDiagnostic] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    skipped_empty: int = 0
    skipped_disabled: int = 0
    skipped_unsupported: int = 0


@dataclass(frozen=True)
class KnowledgeProjectionRequest:
    """In-memory projection inputs (no report-file reads)."""

    context: ProjectionContext
    repository_root: Path | None = None
    manifest: RepositoryManifest | None = None
    content_reader: RepositoryContentReader | None = None
    findings: tuple[Finding, ...] = ()
    recommendations: tuple[Recommendation, ...] = ()
    evidence_items: tuple[Any, ...] = ()
    assessment_sections: Mapping[str, Any] = field(default_factory=dict)
    report_sections: Mapping[str, Any] = field(default_factory=dict)


ASSESSMENT_SOURCE_TYPES: dict[str, KnowledgeSourceType] = {
    "architecture": KnowledgeSourceType.ARCHITECTURE,
    "technical_debt": KnowledgeSourceType.TECHNICAL_DEBT,
    "dependency": KnowledgeSourceType.DEPENDENCY,
    "security": KnowledgeSourceType.SECURITY,
    "test": KnowledgeSourceType.TEST,
    "testing": KnowledgeSourceType.TEST,
    "cloud": KnowledgeSourceType.CLOUD,
    "ai_readiness": KnowledgeSourceType.AI_READINESS,
    "performance": KnowledgeSourceType.PERFORMANCE,
}


def confidence_from_metadata(metadata: Mapping[str, Any] | None) -> str | None:
    if not metadata:
        return None
    value = metadata.get("confidence")
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def first_evidence_path(evidence: Sequence[Any]) -> str | None:
    for item in evidence:
        path = getattr(item, "path", None)
        if path:
            return str(path)
    return None
