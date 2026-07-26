"""Citation and grounding validation for grounded answers."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from codestrata_platform.rag.domain.answering import (
    AnswerCitation,
    AnswerDiagnostic,
    AnswerStatement,
    AnswerStatementType,
)
from codestrata_platform.rag.domain.retrieval import RetrievalHit, RetrievalScope

_WHITESPACE = re.compile(r"\s+")


def normalize_for_grounding(text: str) -> str:
    return _WHITESPACE.sub(" ", text).strip().lower()


def token_overlap_ratio(left: str, right: str) -> float:
    left_tokens = set(normalize_for_grounding(left).split())
    right_tokens = set(normalize_for_grounding(right).split())
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / float(len(left_tokens))


def citation_from_hit(hit: RetrievalHit, *, excerpt: str | None = None) -> AnswerCitation:
    return AnswerCitation(
        citation_label=hit.citation_label,
        record_id=hit.record_id,
        chunk_id=hit.chunk_id,
        document_id=hit.document_id,
        source_type=hit.source_type,
        intelligence_pack=hit.intelligence_pack,
        file_path=hit.file_path,
        symbol_name=hit.symbol_name,
        finding_id=hit.finding_id,
        rule_id=hit.rule_id,
        scan_id=hit.scan_id,
        commit_sha=hit.commit_sha,
        traceability=dict(hit.traceability),
        excerpt=excerpt if excerpt is not None else (hit.content or None),
    )


def validate_scope_hit(hit: RetrievalHit, scope: RetrievalScope) -> str | None:
    if hit.tenant_id != scope.tenant_id:
        return "tenant mismatch"
    if hit.repository_id != scope.repository_id:
        return "repository mismatch"
    if scope.scan_id is not None and hit.scan_id != scope.scan_id:
        return "scan mismatch"
    if scope.branch is not None and hit.branch != scope.branch:
        return "branch mismatch"
    if scope.commit_sha is not None and hit.commit_sha != scope.commit_sha:
        return "commit mismatch"
    return None


def statement_is_grounded(
    statement: AnswerStatement,
    *,
    hits_by_label: Mapping[str, RetrievalHit],
    min_overlap: float = 0.45,
) -> tuple[bool, str | None]:
    """Return whether statement text is supported by cited hit content."""

    if statement.statement_type in {
        AnswerStatementType.INSUFFICIENT_EVIDENCE,
        AnswerStatementType.LIMITATION,
    }:
        return True, None

    if not statement.citation_labels:
        return False, "uncited factual statement"

    normalized_statement = normalize_for_grounding(statement.text)
    if not normalized_statement:
        return False, "empty statement"

    for label in statement.citation_labels:
        hit = hits_by_label.get(label)
        if hit is None:
            return False, f"unknown citation {label}"
        content = hit.content or ""
        if not content.strip():
            return False, "missing source content"
        normalized_content = normalize_for_grounding(content)
        if normalized_statement in normalized_content:
            return True, None
        if token_overlap_ratio(statement.text, content) >= min_overlap:
            return True, None
    return False, "unsupported statement"


def validate_and_filter_statements(
    statements: Sequence[AnswerStatement],
    citations: Sequence[AnswerCitation],
    *,
    hits: Sequence[RetrievalHit],
    scope: RetrievalScope,
    require_citations: bool,
) -> tuple[
    list[AnswerStatement],
    list[AnswerCitation],
    list[AnswerDiagnostic],
    int,
]:
    """Validate citations/grounding; return accepted statements and citations."""

    hits_by_label = {hit.citation_label: hit for hit in hits}
    diagnostics: list[AnswerDiagnostic] = []
    accepted: list[AnswerStatement] = []
    excluded = 0

    # Scope-check hits first.
    for hit in hits:
        mismatch = validate_scope_hit(hit, scope)
        if mismatch:
            diagnostics.append(
                AnswerDiagnostic(
                    code="scope_mismatch",
                    message=f"retrieval hit {hit.citation_label} failed scope check: {mismatch}",
                    severity="error",
                    citation_label=hit.citation_label,
                )
            )

    valid_labels = {
        hit.citation_label
        for hit in hits
        if validate_scope_hit(hit, scope) is None
    }

    citation_by_label = {item.citation_label: item for item in citations}
    used_labels: list[str] = []

    for statement in statements:
        # Drop unknown / orphan citation labels.
        cleaned_labels: list[str] = []
        for label in statement.citation_labels:
            if label not in hits_by_label:
                diagnostics.append(
                    AnswerDiagnostic(
                        code="unknown_citation",
                        message=f"unknown citation {label}",
                        severity="error",
                        statement_id=statement.statement_id,
                        citation_label=label,
                    )
                )
                continue
            if label not in valid_labels:
                diagnostics.append(
                    AnswerDiagnostic(
                        code="scope_mismatch",
                        message=f"citation {label} outside request scope",
                        severity="error",
                        statement_id=statement.statement_id,
                        citation_label=label,
                    )
                )
                continue
            cleaned_labels.append(label)

        # Deduplicate labels while preserving order.
        seen: set[str] = set()
        unique_labels = []
        for label in cleaned_labels:
            if label in seen:
                continue
            seen.add(label)
            unique_labels.append(label)

        factual = statement.statement_type not in {
            AnswerStatementType.INSUFFICIENT_EVIDENCE,
            AnswerStatementType.LIMITATION,
        }
        if require_citations and factual and not unique_labels:
            excluded += 1
            diagnostics.append(
                AnswerDiagnostic(
                    code="uncited_factual_statement",
                    message="excluded factual statement without valid citations",
                    severity="warning",
                    statement_id=statement.statement_id,
                )
            )
            continue

        updated = AnswerStatement(
            statement_id=statement.statement_id,
            sequence=len(accepted),
            text=statement.text,
            citation_labels=tuple(unique_labels),
            confidence=statement.confidence,
            evidence_strength=statement.evidence_strength,
            statement_type=statement.statement_type,
        )
        grounded, reason = statement_is_grounded(
            updated, hits_by_label=hits_by_label
        )
        if not grounded:
            excluded += 1
            code = "unsupported_statement"
            if reason == "uncited factual statement":
                code = "uncited_factual_statement"
            elif reason and reason.startswith("unknown"):
                code = "unknown_citation"
            elif reason == "missing source content":
                code = "missing_source_content"
            diagnostics.append(
                AnswerDiagnostic(
                    code=code,
                    message=reason or "statement failed grounding validation",
                    severity="warning",
                    statement_id=statement.statement_id,
                )
            )
            continue

        accepted.append(updated)
        for label in unique_labels:
            if label not in used_labels:
                used_labels.append(label)

    # Build citations in retrieval order among used labels.
    ordered_citations: list[AnswerCitation] = []
    for hit in hits:
        label = hit.citation_label
        if label not in used_labels:
            continue
        existing = citation_by_label.get(label)
        if existing is not None:
            # Ensure metadata matches the hit.
            ordered_citations.append(
                AnswerCitation(
                    citation_label=label,
                    record_id=hit.record_id,
                    chunk_id=hit.chunk_id,
                    document_id=hit.document_id,
                    source_type=hit.source_type,
                    intelligence_pack=hit.intelligence_pack,
                    file_path=hit.file_path,
                    symbol_name=hit.symbol_name,
                    finding_id=hit.finding_id,
                    rule_id=hit.rule_id,
                    scan_id=hit.scan_id,
                    commit_sha=hit.commit_sha,
                    traceability=dict(hit.traceability),
                    excerpt=existing.excerpt or hit.content,
                )
            )
        else:
            ordered_citations.append(citation_from_hit(hit))

    # Orphan provider citations (not used by accepted statements) are dropped.
    for label, citation in citation_by_label.items():
        if label not in used_labels:
            diagnostics.append(
                AnswerDiagnostic(
                    code="orphan_citation",
                    message=f"removed unused citation {label}",
                    severity="info",
                    citation_label=citation.citation_label,
                )
            )

    return accepted, ordered_citations, diagnostics, excluded
