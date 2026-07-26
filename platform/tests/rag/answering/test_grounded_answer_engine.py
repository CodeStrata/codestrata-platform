"""Unit tests for grounded answer engine, provider, validation (Phase 5.6)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from codestrata.config.settings import KnowledgeAnsweringSettings, load_settings
from codestrata.services.artifact_serialization import dumps_stable_json
from codestrata_platform.rag.application.answering import (
    AnswerProviderConfigurationError,
    AnswerProviderRequest,
    DeterministicExtractiveAnswerProvider,
    create_answer_provider,
    write_grounded_answer_artifact,
)
from codestrata_platform.rag.application.answering.confidence import calculate_answer_confidence
from codestrata_platform.rag.application.answering.validation import (
    statement_is_grounded,
    validate_and_filter_statements,
)
from codestrata_platform.rag.domain import (
    AnswerCitation,
    AnswerConfidence,
    AnswerStatement,
    AnswerStatementType,
    AnswerStatus,
    AnswerStyle,
    GroundedAnswerRequest,
    RetrievalHit,
    RetrievalScope,
    build_request_fingerprint,
    grounded_answer_result_payload,
)
from rag.answering.helpers import build_engine, record, scope


def test_empty_and_whitespace_question() -> None:
    engine, _, _ = build_engine()
    for question in ("", "   ", "\n\t"):
        result = engine.answer(GroundedAnswerRequest(question=question, scope=scope()))
        assert result.status == AnswerStatus.FAILED
        assert any(d.code == "empty_query" for d in result.diagnostics)


def test_oversized_question() -> None:
    engine, _, _ = build_engine()
    result = engine.answer(
        GroundedAnswerRequest(
            question="x" * 50,
            scope=scope(),
            max_query_characters=10,
        )
    )
    assert result.status == AnswerStatus.FAILED
    assert any(d.code == "query_too_large" for d in result.diagnostics)


def test_missing_tenant_or_repository() -> None:
    with pytest.raises(ValidationError):
        RetrievalScope(tenant_id="", repository_id="repo-a")
    with pytest.raises(ValidationError):
        RetrievalScope(tenant_id="tenant-a", repository_id=" ")


def test_disabled_answering() -> None:
    engine, _, _ = build_engine(answering_enabled=False)
    result = engine.answer(
        GroundedAnswerRequest(question="architecture organization", scope=scope())
    )
    assert result.status == AnswerStatus.DISABLED
    assert any(d.code == "answer_engine_disabled" for d in result.diagnostics)


def test_stable_request_fingerprint() -> None:
    left = GroundedAnswerRequest(question="hello world", scope=scope(), top_k=5)
    right = GroundedAnswerRequest(question="hello world", scope=scope(), top_k=5)
    assert build_request_fingerprint(left) == build_request_fingerprint(right)


def test_retrieval_disabled() -> None:
    engine, _, _ = build_engine(retrieval_enabled=False)
    result = engine.answer(
        GroundedAnswerRequest(question="architecture", scope=scope())
    )
    assert result.status == AnswerStatus.FAILED
    assert any(d.code == "retrieval_disabled" for d in result.diagnostics)


def test_empty_retrieval() -> None:
    engine, _, _ = build_engine()
    result = engine.answer(
        GroundedAnswerRequest(question="architecture organization", scope=scope())
    )
    assert result.status == AnswerStatus.EMPTY
    assert result.answer is not None
    assert "insufficient" in result.answer.summary.lower()


def test_end_to_end_success_and_determinism() -> None:
    engine, store, _ = build_engine()
    store.upsert(
        [
            record(
                "arch",
                "The repository architecture is organized as a layered modular monolith.",
                source_type="architecture",
                file_path="docs/architecture.md",
            ),
            record(
                "sec",
                "A high severity security finding was identified in authentication.",
                source_type="security",
                severity="high",
                finding_id="finding-auth-1",
                file_path="src/auth.py",
            ),
        ]
    )
    request = GroundedAnswerRequest(
        question="How is the repository architecture organized?",
        scope=scope(),
        top_k=5,
        style=AnswerStyle.ARCHITECTURE_EXPLANATION,
    )
    first = engine.answer(request)
    second = engine.answer(request)
    assert first.status in {AnswerStatus.SUCCESS, AnswerStatus.PARTIAL}
    assert first.answer is not None
    assert first.answer.statements
    assert all(stmt.citation_labels for stmt in first.answer.statements)
    assert first.answer.fingerprint == second.answer.fingerprint
    assert dumps_stable_json(grounded_answer_result_payload(first)) == dumps_stable_json(
        grounded_answer_result_payload(second)
    )
    assert first.answer.provider.is_generative_ai is False
    assert first.answer.provider.is_production_model is False


def test_tenant_repository_scan_isolation() -> None:
    engine, store, _ = build_engine()
    store.upsert(
        [
            record(
                "keep",
                "Authentication is implemented in the login controller.",
                tenant_id="t1",
                repository_id="r1",
                scan_id="s1",
            ),
            record(
                "other",
                "Authentication is implemented in the login controller.",
                tenant_id="t2",
                repository_id="r1",
                scan_id="s1",
            ),
            record(
                "other-scan",
                "Authentication is implemented in the login controller.",
                tenant_id="t1",
                repository_id="r1",
                scan_id="s2",
            ),
        ]
    )
    result = engine.answer(
        GroundedAnswerRequest(
            question="Authentication is implemented in the login controller.",
            scope=RetrievalScope(tenant_id="t1", repository_id="r1", scan_id="s1"),
        )
    )
    assert result.status in {AnswerStatus.SUCCESS, AnswerStatus.PARTIAL}
    assert result.answer is not None
    for citation in result.answer.citations:
        assert citation.scan_id == "s1"
    assert result.coverage.retrieval_hits >= 1


def test_deterministic_provider_sentence_preservation() -> None:
    provider = DeterministicExtractiveAnswerProvider(preserve_source_sentences=True)
    hit = RetrievalHit(
        rank=1,
        score=0.9,
        record_id="rec-1",
        citation_label="SRC-001",
        content="Alpha sentence one. Beta sentence two about authentication.",
        document_id="kd:1",
        tenant_id="tenant-a",
        repository_id="repo-a",
    )
    result = provider.generate(
        AnswerProviderRequest(
            question="authentication",
            normalized_question="authentication",
            style=AnswerStyle.CONCISE,
            hits=(hit,),
            citation_labels=("SRC-001",),
            max_statements=2,
        )
    )
    assert result.insufficient_evidence is False
    assert result.statements
    assert all(stmt.citation_labels == ("SRC-001",) for stmt in result.statements)
    assert provider.capabilities().is_generative_ai is False
    assert provider.model_identity().is_production_model is False


def test_provider_no_unsupported_generation() -> None:
    provider = DeterministicExtractiveAnswerProvider()
    hit = RetrievalHit(
        rank=1,
        score=0.5,
        record_id="rec-1",
        citation_label="SRC-001",
        content="Dependency modernization risk for library X is high.",
        tenant_id="tenant-a",
        repository_id="repo-a",
    )
    result = provider.generate(
        AnswerProviderRequest(
            question="dependency modernization risk",
            normalized_question="dependency modernization risk",
            style=AnswerStyle.CONCISE,
            hits=(hit,),
            citation_labels=("SRC-001",),
        )
    )
    for stmt in result.statements:
        assert stmt.text in (hit.content or "")


def test_unknown_and_orphan_citations_filtered() -> None:
    hits = (
        RetrievalHit(
            rank=1,
            score=0.8,
            record_id="rec-1",
            citation_label="SRC-001",
            content="Cloud configuration uses environment profiles.",
            tenant_id="tenant-a",
            repository_id="repo-a",
            document_id="kd:cloud",
        ),
    )
    statements = (
        AnswerStatement(
            statement_id="s1",
            sequence=0,
            text="Cloud configuration uses environment profiles.",
            citation_labels=("SRC-001", "SRC-999"),
            statement_type=AnswerStatementType.FACT,
        ),
        AnswerStatement(
            statement_id="s2",
            sequence=1,
            text="Invented claim without support.",
            citation_labels=("SRC-001",),
            statement_type=AnswerStatementType.FACT,
        ),
    )
    citations = (
        AnswerCitation(
            citation_label="SRC-001",
            record_id="rec-1",
            excerpt="Cloud configuration uses environment profiles.",
        ),
        AnswerCitation(citation_label="SRC-ORPHAN", record_id="rec-x"),
    )
    accepted, out_citations, diagnostics, excluded = validate_and_filter_statements(
        statements,
        citations,
        hits=hits,
        scope=scope(),
        require_citations=True,
    )
    assert len(accepted) == 1
    assert accepted[0].citation_labels == ("SRC-001",)
    assert [c.citation_label for c in out_citations] == ["SRC-001"]
    assert excluded >= 1
    assert any(d.code == "unknown_citation" for d in diagnostics)
    assert any(d.code == "orphan_citation" for d in diagnostics)
    assert any(d.code == "unsupported_statement" for d in diagnostics)


def test_limitation_without_citation_allowed() -> None:
    hits = (
        RetrievalHit(
            rank=1,
            score=0.1,
            record_id="rec-1",
            citation_label="SRC-001",
            content="unrelated content",
            tenant_id="tenant-a",
            repository_id="repo-a",
        ),
    )
    statements = (
        AnswerStatement(
            statement_id="lim",
            sequence=0,
            text="Evidence coverage is limited for this question.",
            citation_labels=(),
            statement_type=AnswerStatementType.LIMITATION,
        ),
    )
    accepted, _, _, excluded = validate_and_filter_statements(
        statements,
        (),
        hits=hits,
        scope=scope(),
        require_citations=True,
    )
    assert len(accepted) == 1
    assert excluded == 0


def test_scope_mismatch_rejected() -> None:
    hits = (
        RetrievalHit(
            rank=1,
            score=0.9,
            record_id="rec-1",
            citation_label="SRC-001",
            content="Testing limitations were identified in integration coverage.",
            tenant_id="other-tenant",
            repository_id="repo-a",
        ),
    )
    statements = (
        AnswerStatement(
            statement_id="s1",
            sequence=0,
            text="Testing limitations were identified in integration coverage.",
            citation_labels=("SRC-001",),
        ),
    )
    accepted, _, diagnostics, excluded = validate_and_filter_statements(
        statements,
        (),
        hits=hits,
        scope=scope(),
        require_citations=True,
    )
    assert accepted == []
    assert excluded == 1
    assert any(d.code == "scope_mismatch" for d in diagnostics)


def test_normalized_containment_and_overlap() -> None:
    hit = RetrievalHit(
        rank=1,
        score=0.7,
        record_id="rec-1",
        citation_label="SRC-001",
        content="Performance risks include N+1 database queries in the owner list.",
        tenant_id="tenant-a",
        repository_id="repo-a",
    )
    ok, _ = statement_is_grounded(
        AnswerStatement(
            statement_id="s1",
            sequence=0,
            text="Performance risks include N+1 database queries in the owner list.",
            citation_labels=("SRC-001",),
        ),
        hits_by_label={"SRC-001": hit},
    )
    assert ok is True
    overlap_ok, _ = statement_is_grounded(
        AnswerStatement(
            statement_id="s2",
            sequence=0,
            text="Performance risks include N+1 database queries",
            citation_labels=("SRC-001",),
        ),
        hits_by_label={"SRC-001": hit},
    )
    assert overlap_ok is True


def test_confidence_bands() -> None:
    hits = [
        RetrievalHit(
            rank=i + 1,
            score=score,
            record_id=f"rec-{i}",
            citation_label=f"SRC-{i+1:03d}",
            content=f"fact {i}",
            document_id=f"kd:{i}",
            file_path=f"f{i}.py",
            tenant_id="tenant-a",
            repository_id="repo-a",
        )
        for i, score in enumerate((0.9, 0.85, 0.8))
    ]
    statements = [
        AnswerStatement(
            statement_id=f"s{i}",
            sequence=i,
            text=f"fact {i}",
            citation_labels=(hit.citation_label,),
        )
        for i, hit in enumerate(hits[:2])
    ]
    high = calculate_answer_confidence(
        statements=statements,
        citations_used=2,
        hits=hits,
        grounding_exclusions=0,
        minimum_supporting_sources=1,
    )
    assert high == AnswerConfidence.HIGH

    low = calculate_answer_confidence(
        statements=[
            AnswerStatement(
                statement_id="only",
                sequence=0,
                text="fact 0",
                citation_labels=("SRC-001",),
            )
        ],
        citations_used=1,
        hits=hits[:1],
        grounding_exclusions=2,
        minimum_supporting_sources=1,
    )
    assert low in {AnswerConfidence.LOW, AnswerConfidence.MEDIUM}

    none = calculate_answer_confidence(
        statements=(),
        citations_used=0,
        hits=(),
        grounding_exclusions=0,
        minimum_supporting_sources=1,
    )
    assert none == AnswerConfidence.NONE


def test_max_statements_limit() -> None:
    engine, store, _ = build_engine()
    store.upsert(
        [
            record(
                f"doc-{i}",
                f"Technical debt recommendation {i}: refactor module {i}.",
                source_type="recommendation",
                document_id=f"kd:{i}",
            )
            for i in range(6)
        ]
    )
    result = engine.answer(
        GroundedAnswerRequest(
            question="What technical-debt recommendations were generated?",
            scope=scope(),
            max_statements=2,
            top_k=10,
        )
    )
    assert result.answer is not None
    assert len(result.answer.statements) <= 2


def test_artifact_byte_identical_and_sanitized(tmp_path: Path) -> None:
    engine, store, _ = build_engine()
    store.upsert(
        [
            record(
                "arch",
                "The repository architecture is organized around domain packages.",
                source_type="architecture",
            )
        ]
    )
    request = GroundedAnswerRequest(
        question="How is the repository architecture organized?",
        scope=scope(),
    )
    first = engine.answer(request)
    second = engine.answer(request)
    path_a = write_grounded_answer_artifact(
        first, tmp_path / "a", enabled=True, filename="repository-grounded-answer.json"
    )
    path_b = write_grounded_answer_artifact(
        second, tmp_path / "b", enabled=True, filename="repository-grounded-answer.json"
    )
    assert path_a is not None and path_b is not None
    text_a = path_a.read_text(encoding="utf-8")
    text_b = path_b.read_text(encoding="utf-8")
    assert text_a == text_b
    assert "embedding" not in text_a.lower() or '"embedding"' not in text_a
    assert "password" not in text_a
    assert "postgresql://" not in text_a


def test_factory_deterministic_and_reserved() -> None:
    from codestrata_platform.rag.application.answering.bedrock import BedrockAnswerProvider

    provider = create_answer_provider(
        KnowledgeAnsweringSettings(provider="deterministic_extractive")
    )
    assert isinstance(provider, DeterministicExtractiveAnswerProvider)

    bedrock = create_answer_provider(KnowledgeAnsweringSettings(provider="bedrock"))
    assert isinstance(bedrock, BedrockAnswerProvider)

    with pytest.raises(AnswerProviderConfigurationError, match="not implemented"):
        create_answer_provider(KnowledgeAnsweringSettings(provider="anthropic"))
    with pytest.raises(AnswerProviderConfigurationError, match="unknown"):
        # Bypass settings validator by constructing via model_construct
        create_answer_provider(
            KnowledgeAnsweringSettings.model_construct(provider="mystery")
        )


def test_settings_load_answering_defaults(tmp_path: Path) -> None:
    config_file = tmp_path / "codestrata.toml"
    config_file.write_text(
        """
        [repository]
        path = "test-fixtures/sample-js-app"

        [knowledge.answering]
        enabled = true
        provider = "deterministic_extractive"
        style = "detailed"
        max_statements = 5

        [knowledge.answering.deterministic_extractive]
        max_excerpt_characters = 400
        """,
        encoding="utf-8",
    )
    settings = load_settings(config_file)
    assert settings.knowledge.answering.enabled is True
    assert settings.knowledge.answering.style == "detailed"
    assert settings.knowledge.answering.max_statements == 5
    assert settings.knowledge.answering.deterministic_extractive.max_excerpt_characters == 400


def test_fail_on_insufficient_evidence() -> None:
    engine, _, _ = build_engine()
    result = engine.answer(
        GroundedAnswerRequest(
            question="nonexistent topic xyzzy",
            scope=scope(),
            fail_on_insufficient_evidence=True,
        )
    )
    assert result.status in {AnswerStatus.FAILED, AnswerStatus.EMPTY}
