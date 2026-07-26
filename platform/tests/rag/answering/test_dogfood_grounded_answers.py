"""Dogfood: grounded extractive answers (Phase 5.6 — not production AI).

Runs deterministic extractive answering against in-memory fixtures that mimic
CodeStrata, Spring Petclinic, and a synthetic multi-language corpus.

Label: TEST/DOGFOOD OUTPUT — DeterministicExtractiveAnswerProvider is not a
production language model.
"""

from __future__ import annotations

import json
from pathlib import Path

from codestrata.config.settings import (
    KnowledgeAnsweringSettings,
    KnowledgeEmbeddingSettings,
    KnowledgeRetrievalSettings,
)
from codestrata.services.artifact_serialization import dumps_stable_json
from codestrata_platform.rag.application.answering import (
    DeterministicExtractiveAnswerProvider,
    GroundedAnswerEngine,
)
from codestrata_platform.rag.application.retrieval import RepositoryRetriever
from codestrata_platform.rag.domain import (
    GroundedAnswerRequest,
    RetrievalScope,
    VectorRecord,
)
from codestrata_platform.rag.embedding import DeterministicEmbeddingProvider
from codestrata_platform.rag.vector_store import InMemoryVectorStore

QUESTIONS = [
    "How is the repository architecture organized?",
    "What are the most important security findings?",
    "Which dependencies create modernization risk?",
    "Where is authentication implemented?",
    "What testing limitations were identified?",
    "What performance risks exist?",
    "How is cloud configuration handled?",
    "What technical-debt recommendations were generated?",
]

CORPORA: dict[str, list[tuple[str, str, dict[str, object]]]] = {
    "codestrata": [
        (
            "arch",
            "The CodeStrata architecture is organized as layered application, domain, and infrastructure packages.",  # noqa: E501
            {"source_type": "architecture", "file_path": "ARCHITECTURE.md"},
        ),
        (
            "sec",
            "A high severity security finding notes secret redaction gaps in diagnostic output.",
            {
                "source_type": "security",
                "severity": "high",
                "finding_id": "sec-redact-1",
                "file_path": "src/codestrata/security/database_url.py",
            },
        ),
        (
            "dep",
            "Dependency modernization risk includes pinned transitive packages with outdated majors.",  # noqa: E501
            {"source_type": "dependency", "file_path": "pyproject.toml"},
        ),
        (
            "auth",
            "Authentication for repository access is implemented in repository_auth adapters.",
            {"source_type": "repository_file", "file_path": "src/codestrata/repository_auth/"},
        ),
        (
            "test",
            "Testing limitations include incomplete Docker-backed pgvector coverage in CI.",
            {"source_type": "test", "file_path": "tests/"},
        ),
        (
            "perf",
            "Performance risks include unbounded vector search candidate windows without diversity caps.",  # noqa: E501
            {"source_type": "performance"},
        ),
        (
            "cloud",
            "Cloud configuration is handled via optional AWS and Bedrock settings that remain disabled by default.",  # noqa: E501
            {"source_type": "cloud", "file_path": "codestrata.toml"},
        ),
        (
            "debt",
            "Technical-debt recommendations suggest consolidating report rendering helpers.",
            {"source_type": "recommendation", "file_path": "src/codestrata/reporters/"},
        ),
    ],
    "spring-petclinic": [
        (
            "arch",
            "Spring Petclinic architecture is organized around owners, pets, vets, and visits domain packages.",  # noqa: E501
            {"source_type": "architecture", "file_path": "src/main/java"},
        ),
        (
            "sec",
            "Security findings highlight default in-memory credentials for local demos.",
            {"source_type": "security", "severity": "medium", "finding_id": "sec-demo-1"},
        ),
        (
            "dep",
            "Dependency modernization risk includes Spring Boot and Hibernate version alignment.",
            {"source_type": "dependency", "file_path": "pom.xml"},
        ),
        (
            "auth",
            "Authentication is implemented through Spring Security configuration for web access.",
            {
                "source_type": "repository_file",
                "file_path": "src/main/java/.../SecurityConfiguration.java",
            },
        ),
        (
            "test",
            "Testing limitations include sparse end-to-end coverage for clinic workflows.",
            {"source_type": "test"},
        ),
        (
            "perf",
            "Performance risks include N+1 query patterns when listing owners and pets.",
            {"source_type": "performance"},
        ),
        (
            "cloud",
            "Cloud configuration is handled via Spring profiles and externalized datasource properties.",  # noqa: E501
            {"source_type": "cloud", "file_path": "src/main/resources/application*.yml"},
        ),
        (
            "debt",
            "Technical-debt recommendations include consolidating duplicated controller validation.",  # noqa: E501
            {"source_type": "recommendation"},
        ),
    ],
    "synthetic-multilang": [
        (
            "arch",
            "The synthetic multi-language repository architecture mixes Python services with a TypeScript UI package.",  # noqa: E501
            {"source_type": "architecture", "file_path": "packages/"},
        ),
        (
            "sec",
            "Important security findings include hardcoded API tokens in a sample Node script.",
            {"source_type": "security", "severity": "high", "finding_id": "sec-token-1"},
        ),
        (
            "dep",
            "Dependencies creating modernization risk include legacy lodash and outdated requests.",
            {"source_type": "dependency"},
        ),
        (
            "auth",
            "Authentication is implemented in the Python API middleware JWT validator.",
            {"source_type": "repository_file", "file_path": "services/api/auth.py"},
        ),
        (
            "test",
            "Testing limitations were identified around cross-language contract tests.",
            {"source_type": "test"},
        ),
        (
            "perf",
            "Performance risks exist in the synchronous TypeScript bundle without code splitting.",
            {"source_type": "performance"},
        ),
        (
            "cloud",
            "Cloud configuration is handled through Terraform modules under infra/.",
            {"source_type": "cloud", "file_path": "infra/"},
        ),
        (
            "debt",
            "Technical-debt recommendations were generated to unify lint configs across languages.",
            {"source_type": "recommendation"},
        ),
    ],
}


def _index(corpus_name: str, dimension: int = 32) -> tuple[GroundedAnswerEngine, RetrievalScope]:
    provider = DeterministicEmbeddingProvider(dimension=dimension)
    store = InMemoryVectorStore()
    records: list[VectorRecord] = []
    for entity_id, text, extra in CORPORA[corpus_name]:
        emb = list(provider.embed_text(text).embedding)
        records.append(
            VectorRecord.create(
                entity_id=f"{corpus_name}-{entity_id}",
                embedding=emb,
                text=text,
                metadata={
                    "tenant_id": "dogfood",
                    "repository_id": corpus_name,
                    "scan_id": "scan-dogfood",
                    "document_id": f"kd:{corpus_name}:{entity_id}",
                    "chunk_id": f"kc:{corpus_name}:{entity_id}",
                    "chunk_sequence": 0,
                    "content_hash": f"hash-{corpus_name}-{entity_id}",
                    **extra,
                },
            )
        )
    store.upsert(records)
    retriever = RepositoryRetriever(
        embedding_provider=provider,
        vector_store=store,
        retrieval_settings=KnowledgeRetrievalSettings(enabled=True),
        embedding_settings=KnowledgeEmbeddingSettings(
            enabled=True, provider="deterministic", dimension=dimension
        ),
    )
    engine = GroundedAnswerEngine(
        retriever=retriever,
        answer_provider=DeterministicExtractiveAnswerProvider(),
        answering_settings=KnowledgeAnsweringSettings(enabled=True),
        retrieval_settings=KnowledgeRetrievalSettings(enabled=True),
    )
    scope = RetrievalScope(
        tenant_id="dogfood",
        repository_id=corpus_name,
        scan_id="scan-dogfood",
    )
    return engine, scope


def run_dogfood(output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, object] = {
        "label": "TEST/DOGFOOD — deterministic extractive answers (not production AI)",
        "corpora": {},
    }
    for corpus in CORPORA:
        engine, scope = _index(corpus)
        rows = []
        for question in QUESTIONS:
            request = GroundedAnswerRequest(question=question, scope=scope, top_k=5)
            first = engine.answer(request)
            second = engine.answer(request)
            answer = first.answer
            rows.append(
                {
                    "question": question,
                    "status": first.status.value,
                    "confidence": answer.confidence.value if answer else None,
                    "statements": len(answer.statements) if answer else 0,
                    "citations_used": len(answer.citations) if answer else 0,
                    "files_cited": sorted(
                        {c.file_path for c in answer.citations if c.file_path}
                    )
                    if answer
                    else [],
                    "findings_cited": sorted(
                        {c.finding_id for c in answer.citations if c.finding_id}
                    )
                    if answer
                    else [],
                    "source_types": sorted(
                        {c.source_type for c in answer.citations if c.source_type}
                    )
                    if answer
                    else [],
                    "limitations": list(answer.limitations) if answer else [],
                    "repeated_run_determinism": (
                        answer is not None
                        and second.answer is not None
                        and answer.fingerprint == second.answer.fingerprint
                        and dumps_stable_json(first.model_dump(mode="json"))
                        == dumps_stable_json(second.model_dump(mode="json"))
                    ),
                    "provider": answer.provider.model_dump(mode="json") if answer else None,
                }
            )
        report["corpora"][corpus] = rows  # type: ignore[index]
        (output_dir / f"{corpus}-grounded-answers.json").write_text(
            dumps_stable_json({"corpus": corpus, "answers": rows}),
            encoding="utf-8",
        )
    summary_path = output_dir / "dogfood-summary.json"
    summary_path.write_text(dumps_stable_json(report), encoding="utf-8")
    return report


def test_dogfood_extractive_answers_deterministic(tmp_path: Path) -> None:
    """Dogfood corpora: TEST/DOGFOOD extractive output (not production AI)."""
    report = run_dogfood(tmp_path)
    assert "codestrata" in report["corpora"]
    assert "spring-petclinic" in report["corpora"]
    assert "synthetic-multilang" in report["corpora"]
    for rows in report["corpora"].values():  # type: ignore[union-attr]
        assert len(rows) == len(QUESTIONS)
        for row in rows:
            assert row["repeated_run_determinism"] is True
            assert row["provider"]["is_generative_ai"] is False
            assert row["provider"]["is_production_model"] is False


def main() -> None:
    root = Path(__file__).resolve().parents[5]  # monorepo root
    out = root / "reports" / "grounded-answering-dogfood"
    report = run_dogfood(out)
    print(json.dumps({"wrote": str(out), "corpora": list(CORPORA)}, indent=2))
    for corpus, rows in report["corpora"].items():  # type: ignore[union-attr]
        print(f"\n=== {corpus} (TEST/DOGFOOD extractive) ===")
        for row in rows:  # type: ignore[assignment]
            print(
                f"- {row['status']:22} conf={row['confidence']!s:6} "
                f"stmts={row['statements']} cites={row['citations_used']} "
                f"det={row['repeated_run_determinism']} | {row['question'][:60]}"
            )


if __name__ == "__main__":
    main()
