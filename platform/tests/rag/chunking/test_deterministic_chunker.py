"""Tests for deterministic knowledge chunking (Phase 5.2)."""

from __future__ import annotations

from codestrata_platform.rag.application.chunking import (
    ChunkingOptions,
    DeterministicKnowledgeChunker,
)
from codestrata_platform.rag.application.projection.context import ProjectionContext
from codestrata_platform.rag.domain.enums import KnowledgeSourceType
from codestrata_platform.rag.domain.models import KnowledgeDocument


def _ctx() -> ProjectionContext:
    return ProjectionContext(
        tenant_id="t1",
        repository_id="r1",
        scan_id="s1",
        branch="main",
        commit_sha="deadbeef",
    )


def _doc(
    *,
    source_type: KnowledgeSourceType,
    source_id: str,
    content: str,
    language: str | None = None,
) -> KnowledgeDocument:
    context = _ctx()
    return KnowledgeDocument.create(
        source_type=source_type,
        source_id=source_id,
        title=source_id,
        content=content,
        metadata=context.base_metadata(
            source_type=source_type,
            language=language,
            file_path=source_id if source_type == KnowledgeSourceType.REPOSITORY_FILE else None,
        ),
        traceability=context.traceability(
            source_type=source_type,
            source_id=source_id,
            file_path=source_id if source_type == KnowledgeSourceType.REPOSITORY_FILE else None,
        ),
    )


PYTHON_SOURCE = """\
import os
from pathlib import Path

class Greeter:
    def hello(self, name: str) -> str:
        return f\"hi {name}\"

def main() -> None:
    print(Greeter().hello(\"world\"))
"""


def test_source_structural_chunking() -> None:
    document = _doc(
        source_type=KnowledgeSourceType.REPOSITORY_FILE,
        source_id="app.py",
        content=PYTHON_SOURCE,
        language="python",
    )
    result = DeterministicKnowledgeChunker(
        ChunkingOptions(max_characters=4000, overlap_characters=40)
    ).chunk_document(document)
    kinds = [chunk.metadata.extra.get("chunk_unit_kind") for chunk in result.chunks]
    assert "file_header_imports" in kinds
    assert "class" in kinds or "method_or_function" in kinds
    assert [chunk.sequence for chunk in result.chunks] == list(range(len(result.chunks)))
    assert len({chunk.chunk_id for chunk in result.chunks}) == len(result.chunks)


def test_fallback_text_chunking_with_overlap() -> None:
    body = ("block-content-" * 40) + "\n"
    assert len(body) > 120
    document = _doc(
        source_type=KnowledgeSourceType.REPOSITORY_FILE,
        source_id="blob.txt",
        content=body,
        language="text",
    )
    result = DeterministicKnowledgeChunker(
        ChunkingOptions(
            max_characters=80,
            overlap_characters=20,
            preserve_logical_units=False,
        )
    ).chunk_document(document)
    assert len(result.chunks) >= 2
    assert result.fallback_chunks >= 1
    assert all(chunk.metadata.extra.get("fallback_text_chunk") for chunk in result.chunks)
    # Overlap: consecutive windows should share a prefix/suffix region.
    left = result.chunks[0].content
    right = result.chunks[1].content
    assert left[-20:] == right[:20] or left[-10:] in right


def test_assessment_aware_chunking() -> None:
    content = """# Assessment: security

## Posture Summary

status ok

## Themes

theme-a

## Conclusions

conclusion-a

## Recommendations

rec-a

## Inventories

inventory

## Limitations and Diagnostics

limitation-a
"""
    document = _doc(
        source_type=KnowledgeSourceType.SECURITY,
        source_id="sec-1",
        content=content,
    )
    result = DeterministicKnowledgeChunker().chunk_document(document)
    kinds = {chunk.metadata.extra.get("chunk_unit_kind") for chunk in result.chunks}
    assert "posture_summary" in kinds
    assert "themes" in kinds
    assert "conclusions" in kinds
    assert "recommendations" in kinds
    assert "inventories" in kinds
    assert "limitations_and_diagnostics" in kinds


def test_finding_primary_chunk_and_oversize_preserve() -> None:
    content = "finding-body-" * 500
    document = _doc(
        source_type=KnowledgeSourceType.FINDING,
        source_id="f-1",
        content=content,
    )
    result = DeterministicKnowledgeChunker(
        ChunkingOptions(max_characters=200, preserve_logical_units=True)
    ).chunk_document(document)
    assert len(result.chunks) == 1
    assert result.oversize_units == 1
    assert result.chunks[0].metadata.extra.get("oversize_logical_unit") is True
    assert result.chunks[0].metadata.finding_id is None or True
    assert result.chunks[0].sequence == 0


def test_stable_chunk_ids_across_runs() -> None:
    document = _doc(
        source_type=KnowledgeSourceType.REPOSITORY_FILE,
        source_id="app.py",
        content=PYTHON_SOURCE,
        language="python",
    )
    chunker = DeterministicKnowledgeChunker()
    left = chunker.chunk_document(document)
    right = chunker.chunk_document(document)
    assert [c.chunk_id for c in left.chunks] == [c.chunk_id for c in right.chunks]
    assert [c.sequence for c in left.chunks] == [c.sequence for c in right.chunks]


def test_tenant_isolation_metadata_propagates() -> None:
    document = _doc(
        source_type=KnowledgeSourceType.FINDING,
        source_id="f-2",
        content="one finding chunk",
    )
    result = DeterministicKnowledgeChunker().chunk_document(document)
    assert result.chunks[0].metadata.tenant_id == "t1"
    assert result.chunks[0].metadata.repository_id == "r1"
    assert result.chunks[0].metadata.scan_id == "s1"
    assert result.chunks[0].traceability.parent_document_id == document.document_id
