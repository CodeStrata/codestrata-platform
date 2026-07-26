"""Tests for knowledge document projectors (Phase 5.2)."""

from __future__ import annotations

from pathlib import Path

from aimf.application.knowledge.projection import (
    KnowledgeProjectionRequest,
    ProjectionContext,
    build_knowledge_corpus,
)
from aimf.application.knowledge.projection.projectors import (
    project_assessment_sections,
    project_evidence_items,
    project_findings,
    project_recommendations,
    project_report_sections,
    project_repository_files,
)
from aimf.config.settings import KnowledgeChunkingSettings, KnowledgeProjectionSettings
from aimf.domain.findings.enums import FindingCategory, FindingSeverity
from aimf.domain.findings.models import Finding, FindingEvidence
from aimf.domain.knowledge.enums import KnowledgeSourceType
from aimf.domain.recommendations.enums import (
    RecommendationCategory,
    RecommendationPriority,
)
from aimf.domain.recommendations.models import Recommendation, RecommendationAction
from aimf.domain.repository.enums import (
    HashAlgorithm,
    RepositoryFileKind,
    RepositoryRevisionType,
    RepositorySourceType,
)
from aimf.domain.repository.files import RepositoryFileEntry
from aimf.domain.repository.fingerprints import FileFingerprint
from aimf.domain.repository.identities import RepositoryIdentity, RepositoryRevision
from aimf.domain.repository.manifests import RepositoryManifest
from aimf.domain.repository.paths import RepositoryPath
from aimf.services.artifact_serialization import dumps_stable_json
from aimf.services.inventory.content_reader import LocalFilesystemContentReader


def _context() -> ProjectionContext:
    return ProjectionContext(
        tenant_id="tenant-a",
        repository_id="repo-a",
        scan_id="scan-a",
        branch="main",
        commit_sha="abc123",
        assessment_version="1.0.0",
    )


def _fp(digest: str) -> FileFingerprint:
    return FileFingerprint(algorithm=HashAlgorithm.SHA256, digest=digest)


def _finding() -> Finding:
    return Finding.create(
        rule_id="ARCH-001",
        title="Coupling",
        description="High coupling detected",
        severity=FindingSeverity.HIGH,
        category=FindingCategory.ARCHITECTURE,
        evidence=[
            FindingEvidence(
                evidence_type="file",
                source_id="src/a.py",
                path="src/a.py",
                excerpt="class A",
            )
        ],
        metadata={"confidence": "high"},
        subject_keys=["src/a.py"],
    )


def _recommendation() -> Recommendation:
    return Recommendation.create(
        provider_id="recommendations.core",
        title="Reduce coupling",
        summary="Split module",
        rationale="Finding ARCH-001",
        priority=RecommendationPriority.HIGH,
        category=RecommendationCategory.MAINTAINABILITY,
        related_finding_ids=["finding-1"],
        actions=[
            RecommendationAction(
                order=1,
                title="Extract interface",
                description="Move shared types",
            )
        ],
        subject_keys=["src/a.py"],
    )


def test_finding_projector_metadata_and_traceability() -> None:
    result = project_findings(context=_context(), findings=[_finding()], enabled=True)
    assert len(result.documents) == 1
    doc = result.documents[0]
    assert doc.source_type == KnowledgeSourceType.FINDING
    assert doc.metadata.tenant_id == "tenant-a"
    assert doc.metadata.repository_id == "repo-a"
    assert doc.metadata.scan_id == "scan-a"
    assert doc.metadata.severity == "high"
    assert doc.metadata.confidence == "high"
    assert doc.metadata.file_path == "src/a.py"
    assert doc.traceability.source.finding_id == doc.source_id
    assert doc.traceability.source.rule_id == "ARCH-001"


def test_recommendation_projector() -> None:
    result = project_recommendations(
        context=_context(),
        recommendations=[_recommendation()],
        enabled=True,
    )
    assert len(result.documents) == 1
    assert result.documents[0].source_type == KnowledgeSourceType.RECOMMENDATION


def test_disabled_and_empty_sections() -> None:
    disabled = project_findings(context=_context(), findings=[_finding()], enabled=False)
    assert disabled.skipped_disabled == 1
    assert disabled.documents == []

    empty = project_findings(context=_context(), findings=[], enabled=True)
    assert empty.skipped_empty == 1

    empty_assessment = project_assessment_sections(
        context=_context(),
        assessment_sections={"security": None},
        enabled=True,
    )
    assert empty_assessment.skipped_disabled == 1


def test_assessment_and_report_projectors() -> None:
    class _Section:
        status = "complete"
        assessment_id = "assess-1"
        section_id = "security"
        section_version = "1.2.0"
        finding_ids = ("f1",)
        synthesis = None
        themes = ()
        conclusions = ()
        recommendations = ()
        limitations = ()
        coverage = None
        execution_summary = None
        security_pack_id = "security.core"

    class _Report:
        status = "ready"
        section_id = "report.security"
        title = "Security Intelligence"
        executive_summary = "Ok"
        overall_posture_summary = "stable"
        themes = ()
        conclusions = ()
        recommendations = ()
        limitations = ()
        diagnostics = ()
        inventory_summary = None
        section_version = "1.0.0"
        schema_name = "report.security"
        repository_name = "demo"

    assessment = project_assessment_sections(
        context=_context(),
        assessment_sections={"security": _Section()},
        enabled=True,
    )
    assert len(assessment.documents) == 1
    assert assessment.documents[0].source_type == KnowledgeSourceType.SECURITY
    assert "## Posture Summary" in assessment.documents[0].content

    report = project_report_sections(
        context=_context(),
        report_sections={"security": _Report()},
        enabled=True,
    )
    assert len(report.documents) == 1
    assert report.documents[0].source_type == KnowledgeSourceType.REPORT_SECTION


def test_evidence_projector() -> None:
    from types import SimpleNamespace

    result = project_evidence_items(
        context=_context(),
        evidence_items=[
            SimpleNamespace(
                bundle_id="ev-bundle-1",
                schema_name="repository-security-evidence",
            )
        ],
        enabled=True,
    )
    assert len(result.documents) == 1
    assert result.documents[0].source_type == KnowledgeSourceType.EVIDENCE


def test_repository_file_projector(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "main.py").write_text(
        "import os\n\nclass App:\n    def run(self):\n        return 1\n",
        encoding="utf-8",
    )
    (root / "binary.bin").write_bytes(b"\x00\x01\x02")
    manifest = RepositoryManifest(
        identity=RepositoryIdentity(
            repository_key="demo",
            source_type=RepositorySourceType.LOCAL,
            display_name="demo",
        ),
        revision=RepositoryRevision(
            revision_id="local",
            revision_type=RepositoryRevisionType.WORKING_TREE,
            branch="main",
        ),
        files=(
            RepositoryFileEntry(
                path=RepositoryPath("main.py"),
                file_kind=RepositoryFileKind.SOURCE,
                size_bytes=40,
                fingerprint=_fp("a" * 64),
            ),
            RepositoryFileEntry(
                path=RepositoryPath("binary.bin"),
                file_kind=RepositoryFileKind.UNKNOWN,
                size_bytes=3,
                fingerprint=_fp("b" * 64),
            ),
        ),
    )
    result = project_repository_files(
        context=_context(),
        manifest=manifest,
        content_reader=LocalFilesystemContentReader(root),
        enabled=True,
    )
    assert len(result.documents) == 1
    assert result.documents[0].source_type == KnowledgeSourceType.REPOSITORY_FILE
    assert result.documents[0].metadata.language == "python"
    assert result.skipped_unsupported >= 1


def test_stable_document_ids_and_corpus_fingerprint(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "a.py").write_text("def hello():\n    return 1\n", encoding="utf-8")
    manifest = RepositoryManifest(
        identity=RepositoryIdentity(
            repository_key="demo",
            source_type=RepositorySourceType.LOCAL,
            display_name="demo",
        ),
        revision=RepositoryRevision(
            revision_id="local",
            revision_type=RepositoryRevisionType.WORKING_TREE,
        ),
        files=(
            RepositoryFileEntry(
                path=RepositoryPath("a.py"),
                file_kind=RepositoryFileKind.SOURCE,
                size_bytes=20,
                fingerprint=_fp("c" * 64),
            ),
        ),
    )
    request = KnowledgeProjectionRequest(
        context=_context(),
        repository_root=root,
        manifest=manifest,
        content_reader=LocalFilesystemContentReader(root),
        findings=(_finding(),),
        recommendations=(_recommendation(),),
        assessment_sections={},
        report_sections={},
    )
    settings = KnowledgeProjectionSettings(enabled=True)
    chunking = KnowledgeChunkingSettings(enabled=True, max_characters=200, overlap_characters=20)
    left = build_knowledge_corpus(request, projection=settings, chunking=chunking)
    right = build_knowledge_corpus(request, projection=settings, chunking=chunking)
    assert left.corpus_id == right.corpus_id
    assert left.fingerprint == right.fingerprint
    assert dumps_stable_json(left.model_dump(mode="json")) == dumps_stable_json(
        right.model_dump(mode="json")
    )
    assert left.coverage.document_count >= 3
    assert left.coverage.chunk_count >= left.coverage.document_count
    assert {doc.document_id for doc in left.documents} == {
        doc.document_id for doc in right.documents
    }


def test_projection_disabled_returns_empty_corpus() -> None:
    corpus = build_knowledge_corpus(
        KnowledgeProjectionRequest(context=_context()),
        projection=KnowledgeProjectionSettings(enabled=False),
        chunking=KnowledgeChunkingSettings(enabled=False),
    )
    assert corpus.documents == ()
    assert corpus.chunks == ()
    assert any(item.code == "projection_disabled" for item in corpus.diagnostics)
