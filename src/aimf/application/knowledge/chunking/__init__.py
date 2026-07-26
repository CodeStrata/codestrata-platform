"""Deterministic knowledge chunking (Phase 5.2)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol

from aimf.domain.knowledge.corpus import KnowledgeDiagnostic
from aimf.domain.knowledge.enums import KnowledgeSourceType
from aimf.domain.knowledge.metadata import KnowledgeMetadata, KnowledgeTraceability
from aimf.domain.knowledge.models import KnowledgeChunk, KnowledgeDocument
from aimf.domain.knowledge.schemas import (
    DETERMINISTIC_CHUNKER_SCHEMA_NAME,
    DETERMINISTIC_CHUNKER_SCHEMA_VERSION,
)

_HEADING_RE = re.compile(r"^## (.+)\s*$", re.MULTILINE)
_PYTHON_DEF_RE = re.compile(r"^(?:async\s+def|def|class)\s+\w+", re.MULTILINE)
_BRACE_TYPE_RE = re.compile(
    r"^(?:export\s+)?(?:public\s+|private\s+|protected\s+|static\s+)*"
    r"(?:class|interface|enum|function|func|fn|struct|impl)\b",
    re.MULTILINE,
)
_IMPORT_RE = re.compile(
    r"^(?:import\s|from\s+\S+\s+import|package\s|using\s|#include\s|require\(|"
    r"@import\s|export\s+\{)",
    re.MULTILINE,
)


@dataclass(frozen=True, slots=True)
class ChunkingOptions:
    max_characters: int = 4000
    overlap_characters: int = 400
    preserve_logical_units: bool = True
    strategy: str = "deterministic"


@dataclass
class ChunkingResult:
    chunks: list[KnowledgeChunk] = field(default_factory=list)
    diagnostics: list[KnowledgeDiagnostic] = field(default_factory=list)
    oversize_units: int = 0
    fallback_chunks: int = 0


class KnowledgeChunker(Protocol):
    """Provider-neutral chunker contract."""

    def chunk_document(self, document: KnowledgeDocument) -> ChunkingResult:
        """Chunk one knowledge document deterministically."""

    def chunk_documents(self, documents: Sequence[KnowledgeDocument]) -> ChunkingResult:
        """Chunk many documents with stable document order."""


def _with_chunk_meta(
    base: KnowledgeMetadata,
    *,
    unit_kind: str,
    oversize: bool = False,
    fallback: bool = False,
) -> KnowledgeMetadata:
    extra = dict(base.extra)
    extra["chunk_unit_kind"] = unit_kind
    extra["chunker"] = DETERMINISTIC_CHUNKER_SCHEMA_NAME
    extra["chunker_version"] = DETERMINISTIC_CHUNKER_SCHEMA_VERSION
    if oversize:
        extra["oversize_logical_unit"] = True
    if fallback:
        extra["fallback_text_chunk"] = True
    return KnowledgeMetadata(
        tenant_id=base.tenant_id,
        repository_id=base.repository_id,
        scan_id=base.scan_id,
        branch=base.branch,
        commit_sha=base.commit_sha,
        language=base.language,
        framework=base.framework,
        source_type=base.source_type,
        intelligence_pack=base.intelligence_pack,
        assessment_version=base.assessment_version,
        finding_id=base.finding_id,
        rule_id=base.rule_id,
        severity=base.severity,
        confidence=base.confidence,
        file_path=base.file_path,
        symbol_name=base.symbol_name,
        content_hash=base.content_hash,
        extra=extra,
    )


def _child_trace(
    document: KnowledgeDocument,
    *,
    notes: str,
) -> KnowledgeTraceability:
    return KnowledgeTraceability(
        source=document.traceability.source,
        source_id=document.traceability.source_id,
        assessment_version=document.traceability.assessment_version,
        parent_document_id=document.document_id,
        notes=notes,
    )


def _bounded_windows(
    text: str,
    *,
    max_characters: int,
    overlap_characters: int,
) -> list[str]:
    if max_characters <= 0:
        raise ValueError("max_characters must be positive")
    overlap = max(0, min(overlap_characters, max_characters - 1))
    if len(text) <= max_characters:
        return [text]
    windows: list[str] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + max_characters, length)
        windows.append(text[start:end])
        if end >= length:
            break
        start = max(0, end - overlap)
        if start >= end:
            start = end
    return windows


def _split_structural_units(text: str, *, language: str | None) -> list[tuple[str, str]]:
    """Split source into header/imports, type/function units, and remainder."""

    lines = text.splitlines(keepends=True)
    if not lines:
        return []

    import_end = 0
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "//", "/*", "*", "<!--")):
            import_end = index + 1
            continue
        if _IMPORT_RE.match(stripped):
            import_end = index + 1
            continue
        break

    units: list[tuple[str, str]] = []
    header = "".join(lines[:import_end])
    body_lines = lines[import_end:]
    if header.strip():
        units.append(("file_header_imports", header))

    body = "".join(body_lines)
    if not body.strip():
        return units or [("file", text)]

    lang = (language or "").lower()
    if lang in {"python"} or (not lang and _PYTHON_DEF_RE.search(body)):
        starts = [match.start() for match in _PYTHON_DEF_RE.finditer(body)]
    else:
        starts = [match.start() for match in _BRACE_TYPE_RE.finditer(body)]

    if not starts:
        # Configuration / prose: blank-line blocks, else whole body.
        blocks = re.split(r"\n\s*\n", body)
        if len(blocks) > 1:
            for block in blocks:
                if block.strip():
                    kind = (
                        "configuration_block"
                        if lang in {"yaml", "toml", "json", "xml"}
                        else ("text_block")
                    )
                    units.append((kind, block if block.endswith("\n") else block + "\n"))
            return units
        units.append(("file_body", body))
        return units

    starts.append(len(body))
    cursor = 0
    if starts[0] > 0:
        preamble = body[: starts[0]]
        if preamble.strip():
            units.append(("preamble", preamble))
        cursor = starts[0]
    for index in range(len(starts) - 1):
        start = starts[index]
        end = starts[index + 1]
        chunk = body[start:end]
        if not chunk.strip():
            continue
        first = chunk.lstrip().splitlines()[0] if chunk.strip() else ""
        kind = (
            "class"
            if re.match(r"^(?:export\s+)?(?:public\s+|private\s+)*class\b", first)
            else ("method_or_function")
        )
        if first.startswith("class ") or first.startswith("class\t"):
            kind = "class"
        elif first.startswith("def ") or first.startswith("async def "):
            kind = "method_or_function"
        units.append((kind, chunk))
        cursor = end
    _ = cursor
    return units or [("file", text)]


def _split_assessment_sections(text: str) -> list[tuple[str, str]]:
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        return [("document", text)]
    units: list[tuple[str, str]] = []
    title = text[: matches[0].start()]
    if title.strip():
        units.append(("title", title))
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        heading = match.group(1).strip().lower()
        body = text[start:end]
        if "posture" in heading:
            kind = "posture_summary"
        elif "theme" in heading:
            kind = "themes"
        elif "conclusion" in heading:
            kind = "conclusions"
        elif "recommendation" in heading:
            kind = "recommendations"
        elif "inventor" in heading:
            kind = "inventories"
        elif "limitation" in heading or "diagnostic" in heading:
            kind = "limitations_and_diagnostics"
        elif "heading hierarchy" in heading:
            kind = "heading_hierarchy"
        else:
            kind = "section"
        units.append((kind, body))
    return units


class DeterministicKnowledgeChunker:
    """Deterministic multi-strategy chunker (no LLM / semantic splitting)."""

    def __init__(self, options: ChunkingOptions | None = None) -> None:
        self._options = options or ChunkingOptions()

    @property
    def options(self) -> ChunkingOptions:
        return self._options

    def chunk_documents(self, documents: Sequence[KnowledgeDocument]) -> ChunkingResult:
        combined = ChunkingResult()
        for document in sorted(
            documents,
            key=lambda item: (str(item.source_type), item.source_id, item.document_id),
        ):
            part = self.chunk_document(document)
            combined.chunks.extend(part.chunks)
            combined.diagnostics.extend(part.diagnostics)
            combined.oversize_units += part.oversize_units
            combined.fallback_chunks += part.fallback_chunks
        return combined

    def chunk_document(self, document: KnowledgeDocument) -> ChunkingResult:
        result = ChunkingResult()
        source_type = document.source_type
        if source_type == KnowledgeSourceType.REPOSITORY_FILE:
            units = _split_structural_units(
                document.content,
                language=document.metadata.language,
            )
        elif source_type in {
            KnowledgeSourceType.ARCHITECTURE,
            KnowledgeSourceType.TECHNICAL_DEBT,
            KnowledgeSourceType.DEPENDENCY,
            KnowledgeSourceType.SECURITY,
            KnowledgeSourceType.TEST,
            KnowledgeSourceType.CLOUD,
            KnowledgeSourceType.AI_READINESS,
            KnowledgeSourceType.PERFORMANCE,
            KnowledgeSourceType.EVIDENCE,
            KnowledgeSourceType.REPORT_SECTION,
        }:
            units = _split_assessment_sections(document.content)
        elif source_type == KnowledgeSourceType.FINDING:
            units = [("finding_primary", document.content)]
        elif source_type == KnowledgeSourceType.RECOMMENDATION:
            units = [("recommendation_primary", document.content)]
        else:
            units = [("document", document.content)]

        sequence = 0
        for unit_kind, unit_text in units:
            if not unit_text.strip():
                continue
            emitted = self._emit_unit(
                document,
                unit_kind=unit_kind,
                unit_text=unit_text,
                start_sequence=sequence,
                result=result,
            )
            sequence += emitted
        return result

    def _emit_unit(
        self,
        document: KnowledgeDocument,
        *,
        unit_kind: str,
        unit_text: str,
        start_sequence: int,
        result: ChunkingResult,
    ) -> int:
        options = self._options
        max_chars = options.max_characters
        if len(unit_text) <= max_chars:
            result.chunks.append(
                KnowledgeChunk.create(
                    document_id=document.document_id,
                    sequence=start_sequence,
                    content=unit_text,
                    metadata=_with_chunk_meta(document.metadata, unit_kind=unit_kind),
                    traceability=_child_trace(document, notes=f"unit={unit_kind}"),
                )
            )
            return 1

        result.oversize_units += 1
        if options.preserve_logical_units and unit_kind in {
            "finding_primary",
            "recommendation_primary",
            "class",
            "method_or_function",
            "posture_summary",
            "themes",
            "conclusions",
            "recommendations",
            "inventories",
            "limitations_and_diagnostics",
        }:
            # Prefer one oversize logical unit; record in metadata.
            result.chunks.append(
                KnowledgeChunk.create(
                    document_id=document.document_id,
                    sequence=start_sequence,
                    content=unit_text,
                    metadata=_with_chunk_meta(
                        document.metadata,
                        unit_kind=unit_kind,
                        oversize=True,
                    ),
                    traceability=_child_trace(
                        document,
                        notes=f"unit={unit_kind};oversize=true",
                    ),
                )
            )
            result.diagnostics.append(
                KnowledgeDiagnostic(
                    code="oversize_logical_unit",
                    message=(
                        f"Preserved oversize logical unit '{unit_kind}' "
                        f"({len(unit_text)} chars) for document {document.document_id}"
                    ),
                    source_type=str(document.source_type),
                    source_id=document.source_id,
                    severity="warning",
                )
            )
            return 1

        windows = _bounded_windows(
            unit_text,
            max_characters=max_chars,
            overlap_characters=options.overlap_characters,
        )
        for offset, window in enumerate(windows):
            result.fallback_chunks += 1
            result.chunks.append(
                KnowledgeChunk.create(
                    document_id=document.document_id,
                    sequence=start_sequence + offset,
                    content=window,
                    metadata=_with_chunk_meta(
                        document.metadata,
                        unit_kind=unit_kind,
                        oversize=True,
                        fallback=True,
                    ),
                    traceability=_child_trace(
                        document,
                        notes=f"unit={unit_kind};fallback_window={offset}",
                    ),
                )
            )
        result.diagnostics.append(
            KnowledgeDiagnostic(
                code="fallback_text_chunking",
                message=(
                    f"Applied bounded fallback chunking to '{unit_kind}' "
                    f"({len(windows)} windows) for document {document.document_id}"
                ),
                source_type=str(document.source_type),
                source_id=document.source_id,
            )
        )
        return len(windows)
