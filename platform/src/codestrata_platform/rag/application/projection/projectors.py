"""Individual knowledge document projectors."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from codestrata.domain.findings.models import Finding
from codestrata.domain.recommendations.models import Recommendation
from codestrata.domain.repository.manifests import RepositoryManifest
from codestrata.services.inventory.content_reader import RepositoryContentReader
from codestrata_platform.rag.application.projection.context import (
    ASSESSMENT_SOURCE_TYPES,
    ProjectionContext,
    ProjectorResult,
    confidence_from_metadata,
    first_evidence_path,
)
from codestrata_platform.rag.application.projection.rendering import (
    render_assessment_content,
    render_evidence_content,
    render_finding_content,
    render_recommendation_content,
    render_report_section_content,
)
from codestrata_platform.rag.domain.corpus import KnowledgeDiagnostic
from codestrata_platform.rag.domain.enums import KnowledgeSourceType
from codestrata_platform.rag.domain.identifiers import content_hash
from codestrata_platform.rag.domain.models import KnowledgeDocument

_TEXT_EXTENSIONS = frozenset(
    {
        ".py",
        ".pyi",
        ".java",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".go",
        ".rb",
        ".php",
        ".cs",
        ".kt",
        ".kts",
        ".scala",
        ".rs",
        ".c",
        ".cc",
        ".cpp",
        ".h",
        ".hpp",
        ".m",
        ".mm",
        ".swift",
        ".sql",
        ".sh",
        ".bash",
        ".zsh",
        ".xml",
        ".html",
        ".htm",
        ".css",
        ".scss",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".conf",
        ".properties",
        ".gradle",
        ".md",
        ".txt",
        ".dockerfile",
        ".gitignore",
        ".env.example",
    }
)
_MAX_FILE_BYTES = 512_000
_EMPTY_STATUSES = frozenset(
    {
        "empty",
        "analytically_empty",
        "not_configured",
        "disabled",
        "unavailable",
        "skipped",
    }
)


def _extension(path: str) -> str:
    name = path.rsplit("/", 1)[-1].lower()
    if "." not in name:
        if name in {"dockerfile", "makefile", "jenkinsfile"}:
            return f".{name}"
        return ""
    return "." + name.rsplit(".", 1)[-1]


def _language_for_path(path: str) -> str | None:
    ext = _extension(path)
    mapping = {
        ".py": "python",
        ".java": "java",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".go": "go",
        ".rb": "ruby",
        ".php": "php",
        ".cs": "csharp",
        ".kt": "kotlin",
        ".kts": "kotlin",
        ".xml": "xml",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".toml": "toml",
        ".json": "json",
        ".md": "markdown",
        ".gradle": "groovy",
    }
    return mapping.get(ext)


def project_repository_files(
    *,
    context: ProjectionContext,
    manifest: RepositoryManifest | None,
    content_reader: RepositoryContentReader | None,
    enabled: bool,
) -> ProjectorResult:
    result = ProjectorResult()
    if not enabled:
        result.skipped_disabled += 1
        result.diagnostics.append(
            KnowledgeDiagnostic(
                code="repository_files_disabled",
                message="Repository file projection disabled by configuration",
                source_type=KnowledgeSourceType.REPOSITORY_FILE.value,
            )
        )
        return result
    if manifest is None or content_reader is None:
        result.skipped_unsupported += 1
        result.limitations.append(
            "Repository file projection skipped: manifest or content reader unavailable"
        )
        result.diagnostics.append(
            KnowledgeDiagnostic(
                code="repository_files_unavailable",
                message="Manifest or content reader not provided",
                source_type=KnowledgeSourceType.REPOSITORY_FILE.value,
                severity="warning",
            )
        )
        return result

    for entry in sorted(manifest.files, key=lambda item: str(item.path)):
        path = str(entry.path)
        ext = _extension(path)
        if ext not in _TEXT_EXTENSIONS and entry.language is None:
            result.skipped_unsupported += 1
            result.diagnostics.append(
                KnowledgeDiagnostic(
                    code="unsupported_file_type",
                    message=f"Skipped non-text repository file: {path}",
                    source_type=KnowledgeSourceType.REPOSITORY_FILE.value,
                    source_id=path,
                )
            )
            continue
        size = entry.size_bytes
        if size is not None and size > _MAX_FILE_BYTES:
            result.skipped_unsupported += 1
            result.diagnostics.append(
                KnowledgeDiagnostic(
                    code="file_too_large",
                    message=f"Skipped oversized repository file ({size} bytes): {path}",
                    source_type=KnowledgeSourceType.REPOSITORY_FILE.value,
                    source_id=path,
                    severity="warning",
                )
            )
            continue
        try:
            raw = content_reader.read(path).data
        except (OSError, ValueError, FileNotFoundError) as error:
            result.skipped_unsupported += 1
            result.diagnostics.append(
                KnowledgeDiagnostic(
                    code="file_read_failed",
                    message=f"Could not read {path}: {error}",
                    source_type=KnowledgeSourceType.REPOSITORY_FILE.value,
                    source_id=path,
                    severity="warning",
                )
            )
            continue
        if len(raw) > _MAX_FILE_BYTES:
            result.skipped_unsupported += 1
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            result.skipped_unsupported += 1
            result.diagnostics.append(
                KnowledgeDiagnostic(
                    code="file_not_utf8",
                    message=f"Skipped non-UTF-8 repository file: {path}",
                    source_type=KnowledgeSourceType.REPOSITORY_FILE.value,
                    source_id=path,
                )
            )
            continue
        if not text.strip():
            result.skipped_empty += 1
            continue
        digest = content_hash(text)
        language = entry.language or _language_for_path(path)
        result.documents.append(
            KnowledgeDocument.create(
                source_type=KnowledgeSourceType.REPOSITORY_FILE,
                source_id=path,
                title=f"Repository file: {path}",
                content=text,
                metadata=context.base_metadata(
                    source_type=KnowledgeSourceType.REPOSITORY_FILE,
                    file_path=path,
                    language=language,
                    content_hash=digest,
                ),
                traceability=context.traceability(
                    source_type=KnowledgeSourceType.REPOSITORY_FILE,
                    source_id=path,
                    file_path=path,
                    notes="repository_manifest_entry",
                ),
            )
        )
    return result


def project_findings(
    *,
    context: ProjectionContext,
    findings: Sequence[Finding],
    enabled: bool,
) -> ProjectorResult:
    result = ProjectorResult()
    if not enabled:
        result.skipped_disabled += 1
        return result
    if not findings:
        result.skipped_empty += 1
        return result
    for finding in sorted(findings, key=lambda item: (item.rule_id, item.id)):
        content = render_finding_content(finding)
        result.documents.append(
            KnowledgeDocument.create(
                source_type=KnowledgeSourceType.FINDING,
                source_id=finding.id,
                title=finding.title,
                content=content,
                metadata=context.base_metadata(
                    source_type=KnowledgeSourceType.FINDING,
                    finding_id=finding.id,
                    rule_id=finding.rule_id,
                    severity=str(finding.severity),
                    confidence=confidence_from_metadata(finding.metadata),
                    file_path=first_evidence_path(finding.evidence),
                    content_hash=content_hash(content),
                    extra={"category": str(finding.category)},
                ),
                traceability=context.traceability(
                    source_type=KnowledgeSourceType.FINDING,
                    source_id=finding.id,
                    finding_id=finding.id,
                    rule_id=finding.rule_id,
                    file_path=first_evidence_path(finding.evidence),
                ),
            )
        )
    return result


def project_recommendations(
    *,
    context: ProjectionContext,
    recommendations: Sequence[Recommendation],
    enabled: bool,
) -> ProjectorResult:
    result = ProjectorResult()
    if not enabled:
        result.skipped_disabled += 1
        return result
    if not recommendations:
        result.skipped_empty += 1
        return result
    for recommendation in sorted(recommendations, key=lambda item: (item.priority, item.id)):
        content = render_recommendation_content(recommendation)
        result.documents.append(
            KnowledgeDocument.create(
                source_type=KnowledgeSourceType.RECOMMENDATION,
                source_id=recommendation.id,
                title=recommendation.title,
                content=content,
                metadata=context.base_metadata(
                    source_type=KnowledgeSourceType.RECOMMENDATION,
                    content_hash=content_hash(content),
                    intelligence_pack=recommendation.provider_id,
                    extra={
                        "priority": str(recommendation.priority),
                        "category": str(recommendation.category),
                    },
                ),
                traceability=context.traceability(
                    source_type=KnowledgeSourceType.RECOMMENDATION,
                    source_id=recommendation.id,
                    notes=f"related_findings={','.join(recommendation.related_finding_ids)}",
                ),
            )
        )
    return result


def _section_is_empty(section_obj: Any) -> bool:
    status = str(getattr(section_obj, "status", "") or "").strip().lower()
    if status in _EMPTY_STATUSES:
        return True
    finding_ids = getattr(section_obj, "finding_ids", None)
    synthesis = getattr(section_obj, "synthesis", None)
    themes = (
        getattr(synthesis, "themes", None)
        if synthesis is not None
        else getattr(section_obj, "themes", None)
    )
    if finding_ids is not None and len(finding_ids) == 0 and not themes:
        # Analytically empty inventory-only sections still project a posture doc
        # unless status marked empty.
        if status in {"", "complete", "completed", "ready", "ok", "partial"}:
            return False
    return False


def project_assessment_sections(
    *,
    context: ProjectionContext,
    assessment_sections: Mapping[str, Any],
    enabled: bool,
) -> ProjectorResult:
    result = ProjectorResult()
    if not enabled:
        result.skipped_disabled += 1
        return result
    if not assessment_sections:
        result.skipped_empty += 1
        return result
    for key in sorted(assessment_sections):
        section_obj = assessment_sections[key]
        source_type = ASSESSMENT_SOURCE_TYPES.get(key)
        if source_type is None:
            result.skipped_unsupported += 1
            result.diagnostics.append(
                KnowledgeDiagnostic(
                    code="unknown_assessment_type",
                    message=f"No projector mapping for assessment key '{key}'",
                    source_type=key,
                    severity="warning",
                )
            )
            continue
        if section_obj is None:
            result.skipped_disabled += 1
            result.diagnostics.append(
                KnowledgeDiagnostic(
                    code="assessment_disabled",
                    message=f"Assessment section '{key}' was not produced",
                    source_type=source_type.value,
                )
            )
            continue
        if _section_is_empty(section_obj):
            result.skipped_empty += 1
            result.diagnostics.append(
                KnowledgeDiagnostic(
                    code="assessment_empty",
                    message=f"Skipped empty assessment section '{key}'",
                    source_type=source_type.value,
                    source_id=str(getattr(section_obj, "assessment_id", key)),
                )
            )
            continue
        content = render_assessment_content(assessment_type=key, section_obj=section_obj)
        source_id = str(
            getattr(section_obj, "assessment_id", None)
            or getattr(section_obj, "section_id", None)
            or key
        )
        pack_id = (
            getattr(section_obj, "performance_pack_id", None)
            or getattr(section_obj, "pack_id", None)
            or getattr(section_obj, f"{key}_pack_id", None)
        )
        section_version = getattr(section_obj, "section_version", None)
        result.documents.append(
            KnowledgeDocument.create(
                source_type=source_type,
                source_id=source_id,
                title=f"{key.replace('_', ' ').title()} assessment",
                content=content,
                metadata=context.base_metadata(
                    source_type=source_type,
                    intelligence_pack=str(pack_id) if pack_id else None,
                    content_hash=content_hash(content),
                    extra={
                        "assessment_status": str(getattr(section_obj, "status", "")),
                        "assessment_section_version": str(section_version or ""),
                    },
                ),
                traceability=context.traceability(
                    source_type=source_type,
                    source_id=source_id,
                    assessment_type=key,
                ),
            )
        )
    return result


def project_report_sections(
    *,
    context: ProjectionContext,
    report_sections: Mapping[str, Any],
    enabled: bool,
) -> ProjectorResult:
    result = ProjectorResult()
    if not enabled:
        result.skipped_disabled += 1
        return result
    if not report_sections:
        result.skipped_empty += 1
        return result
    for key in sorted(report_sections):
        section_obj = report_sections[key]
        if section_obj is None:
            result.skipped_disabled += 1
            continue
        status = str(getattr(section_obj, "status", "") or "").lower()
        if status in _EMPTY_STATUSES:
            result.skipped_empty += 1
            continue
        content = render_report_section_content(section_key=key, section_obj=section_obj)
        source_id = str(getattr(section_obj, "section_id", None) or key)
        result.documents.append(
            KnowledgeDocument.create(
                source_type=KnowledgeSourceType.REPORT_SECTION,
                source_id=source_id,
                title=str(getattr(section_obj, "title", None) or key),
                content=content,
                metadata=context.base_metadata(
                    source_type=KnowledgeSourceType.REPORT_SECTION,
                    content_hash=content_hash(content),
                    extra={"report_section_key": key, "status": status},
                ),
                traceability=context.traceability(
                    source_type=KnowledgeSourceType.REPORT_SECTION,
                    source_id=source_id,
                    report_section=key,
                ),
            )
        )
    return result


def project_evidence_items(
    *,
    context: ProjectionContext,
    evidence_items: Sequence[Any],
    enabled: bool,
) -> ProjectorResult:
    result = ProjectorResult()
    if not enabled:
        result.skipped_disabled += 1
        return result
    if not evidence_items:
        result.skipped_empty += 1
        return result
    for index, evidence_obj in enumerate(evidence_items):
        if evidence_obj is None:
            result.skipped_empty += 1
            continue
        evidence_id = str(
            getattr(evidence_obj, "bundle_id", None)
            or getattr(evidence_obj, "evidence_id", None)
            or getattr(evidence_obj, "schema_name", None)
            or f"evidence-{index}"
        )
        content = render_evidence_content(evidence_id=evidence_id, evidence_obj=evidence_obj)
        result.documents.append(
            KnowledgeDocument.create(
                source_type=KnowledgeSourceType.EVIDENCE,
                source_id=evidence_id,
                title=f"Evidence: {evidence_id}",
                content=content,
                metadata=context.base_metadata(
                    source_type=KnowledgeSourceType.EVIDENCE,
                    content_hash=content_hash(content),
                ),
                traceability=context.traceability(
                    source_type=KnowledgeSourceType.EVIDENCE,
                    source_id=evidence_id,
                    evidence_id=evidence_id,
                ),
            )
        )
    return result
