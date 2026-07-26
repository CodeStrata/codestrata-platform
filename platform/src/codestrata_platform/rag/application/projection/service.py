"""Knowledge projection orchestration service (Phase 5.2)."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from codestrata.config.settings import KnowledgeChunkingSettings, KnowledgeProjectionSettings
from codestrata.services.artifact_serialization import dumps_stable_json
from codestrata_platform.rag.application.chunking import (
    ChunkingOptions,
    DeterministicKnowledgeChunker,
)
from codestrata_platform.rag.application.projection.context import (
    KnowledgeProjectionRequest,
    ProjectorResult,
)
from codestrata_platform.rag.application.projection.projectors import (
    project_assessment_sections,
    project_evidence_items,
    project_findings,
    project_recommendations,
    project_report_sections,
    project_repository_files,
)
from codestrata_platform.rag.domain.corpus import (
    KnowledgeCorpus,
    KnowledgeCorpusCoverage,
    KnowledgeDiagnostic,
    knowledge_corpus_payload,
)
from codestrata_platform.rag.domain.metadata import KnowledgeMetadata
from codestrata_platform.rag.domain.schemas import (
    DETERMINISTIC_CHUNKER_SCHEMA_VERSION,
    KNOWLEDGE_PROJECTION_SCHEMA_VERSION,
)

CORPUS_ARTIFACT_FILENAME = "repository-knowledge-corpus.json"


def _merge_results(*parts: ProjectorResult) -> ProjectorResult:
    merged = ProjectorResult()
    for part in parts:
        merged.documents.extend(part.documents)
        merged.diagnostics.extend(part.diagnostics)
        merged.limitations.extend(part.limitations)
        merged.skipped_empty += part.skipped_empty
        merged.skipped_disabled += part.skipped_disabled
        merged.skipped_unsupported += part.skipped_unsupported
    return merged


def build_knowledge_corpus(
    request: KnowledgeProjectionRequest,
    *,
    projection: KnowledgeProjectionSettings | None = None,
    chunking: KnowledgeChunkingSettings | None = None,
) -> KnowledgeCorpus:
    """Project in-memory assessment outputs and optionally chunk them.

    When ``projection.enabled`` is false, returns an empty corpus with a
    disabled diagnostic (deterministic, no side effects).
    """

    projection_settings = projection or KnowledgeProjectionSettings()
    chunking_settings = chunking or KnowledgeChunkingSettings()
    context = request.context
    corpus_metadata = KnowledgeMetadata(
        tenant_id=context.tenant_id,
        repository_id=context.repository_id,
        scan_id=context.scan_id,
        branch=context.branch,
        commit_sha=context.commit_sha,
        assessment_version=context.assessment_version,
        source_type=None,
        extra={
            "projection_schema_version": KNOWLEDGE_PROJECTION_SCHEMA_VERSION,
            "chunker_schema_version": DETERMINISTIC_CHUNKER_SCHEMA_VERSION,
        },
    )

    if not projection_settings.enabled:
        return KnowledgeCorpus.create(
            documents=(),
            chunks=(),
            coverage=KnowledgeCorpusCoverage(skipped_disabled=1),
            diagnostics=[
                KnowledgeDiagnostic(
                    code="projection_disabled",
                    message="Knowledge projection disabled by configuration",
                )
            ],
            limitations=["knowledge.projection.enabled=false"],
            metadata=corpus_metadata,
            projection_schema_version=KNOWLEDGE_PROJECTION_SCHEMA_VERSION,
            chunker_schema_version=DETERMINISTIC_CHUNKER_SCHEMA_VERSION,
        )

    projected = _merge_results(
        project_repository_files(
            context=context,
            manifest=request.manifest,
            content_reader=request.content_reader,
            enabled=projection_settings.include_repository_files,
        ),
        project_findings(
            context=context,
            findings=request.findings,
            enabled=projection_settings.include_findings,
        ),
        project_recommendations(
            context=context,
            recommendations=request.recommendations,
            enabled=projection_settings.include_recommendations,
        ),
        project_evidence_items(
            context=context,
            evidence_items=request.evidence_items,
            enabled=projection_settings.include_evidence,
        ),
        project_assessment_sections(
            context=context,
            assessment_sections=request.assessment_sections,
            enabled=projection_settings.include_assessments,
        ),
        project_report_sections(
            context=context,
            report_sections=request.report_sections,
            enabled=projection_settings.include_report_sections,
        ),
    )

    chunks = []
    chunk_diagnostics: list[KnowledgeDiagnostic] = []
    oversize_units = 0
    fallback_chunks = 0
    if chunking_settings.enabled:
        if chunking_settings.strategy != "deterministic":
            chunk_diagnostics.append(
                KnowledgeDiagnostic(
                    code="unsupported_chunking_strategy",
                    message=(
                        f"Chunking strategy '{chunking_settings.strategy}' is not "
                        "supported; expected 'deterministic'"
                    ),
                    severity="warning",
                )
            )
        else:
            chunker = DeterministicKnowledgeChunker(
                ChunkingOptions(
                    max_characters=chunking_settings.max_characters,
                    overlap_characters=chunking_settings.overlap_characters,
                    preserve_logical_units=chunking_settings.preserve_logical_units,
                    strategy=chunking_settings.strategy,
                )
            )
            chunk_result = chunker.chunk_documents(projected.documents)
            chunks = list(chunk_result.chunks)
            chunk_diagnostics.extend(chunk_result.diagnostics)
            oversize_units = chunk_result.oversize_units
            fallback_chunks = chunk_result.fallback_chunks
    else:
        chunk_diagnostics.append(
            KnowledgeDiagnostic(
                code="chunking_disabled",
                message="Knowledge chunking disabled by configuration",
            )
        )

    counts: Counter[str] = Counter(str(doc.source_type) for doc in projected.documents)
    coverage = KnowledgeCorpusCoverage(
        document_count=len(projected.documents),
        chunk_count=len(chunks),
        by_source_type=dict(sorted(counts.items())),
        skipped_empty=projected.skipped_empty,
        skipped_disabled=projected.skipped_disabled,
        skipped_unsupported=projected.skipped_unsupported,
        oversize_units=oversize_units,
        fallback_chunks=fallback_chunks,
    )
    diagnostics = list(projected.diagnostics) + chunk_diagnostics
    limitations = list(projected.limitations)
    if not projected.documents:
        limitations.append("Projection produced no knowledge documents")

    return KnowledgeCorpus.create(
        documents=projected.documents,
        chunks=chunks,
        coverage=coverage,
        diagnostics=diagnostics,
        limitations=limitations,
        metadata=corpus_metadata,
        projection_schema_version=KNOWLEDGE_PROJECTION_SCHEMA_VERSION,
        chunker_schema_version=DETERMINISTIC_CHUNKER_SCHEMA_VERSION,
    )


def write_knowledge_corpus_artifact(
    corpus: KnowledgeCorpus,
    run_directory: Path,
    *,
    enabled: bool,
) -> Path | None:
    """Optionally write ``repository-knowledge-corpus.json`` under the run directory."""

    if not enabled:
        return None
    run_directory.mkdir(parents=True, exist_ok=True)
    path = run_directory / CORPUS_ARTIFACT_FILENAME
    text = dumps_stable_json(knowledge_corpus_payload(corpus))
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
    return path
