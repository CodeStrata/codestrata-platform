"""Dogfood Phase 5.5 — repository retrieval over indexed corpora."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aimf.application.knowledge.indexing import (  # noqa: E402
    KnowledgeIndexRequest,
    KnowledgeIndexer,
)
from aimf.application.knowledge.projection import (  # noqa: E402
    KnowledgeProjectionRequest,
    ProjectionContext,
    build_knowledge_corpus,
)
from aimf.application.knowledge.retrieval import (  # noqa: E402
    RepositoryRetriever,
    write_retrieval_result_artifact,
)
from aimf.config.settings import (  # noqa: E402
    KnowledgeChunkingSettings,
    KnowledgeEmbeddingSettings,
    KnowledgeIndexingSettings,
    KnowledgeProjectionSettings,
    KnowledgeRetrievalSettings,
)
from aimf.domain.findings.enums import FindingCategory, FindingSeverity  # noqa: E402
from aimf.domain.findings.models import Finding, FindingEvidence  # noqa: E402
from aimf.domain.knowledge import (  # noqa: E402
    IndexScope,
    RetrievalRequest,
    RetrievalScope,
)
from aimf.domain.repository.enums import (  # noqa: E402
    HashAlgorithm,
    RepositoryFileKind,
    RepositoryRevisionType,
    RepositorySourceType,
)
from aimf.domain.repository.files import RepositoryFileEntry  # noqa: E402
from aimf.domain.repository.fingerprints import hash_bytes  # noqa: E402
from aimf.domain.repository.identities import RepositoryIdentity, RepositoryRevision  # noqa: E402
from aimf.domain.repository.manifests import RepositoryManifest  # noqa: E402
from aimf.domain.repository.paths import RepositoryPath  # noqa: E402
from aimf.infrastructure.embedding import DeterministicEmbeddingProvider  # noqa: E402
from aimf.infrastructure.vector_store import InMemoryVectorStore  # noqa: E402
from aimf.services.inventory.content_reader import LocalFilesystemContentReader  # noqa: E402

QUERIES = [
    "Where is repository architecture defined?",
    "What are the highest-severity security findings?",
    "Which dependencies present modernization risk?",
    "Where is authentication implemented?",
    "What test coverage limitations were identified?",
    "What performance risks were found?",
    "Which files contain cloud configuration?",
    "What recommendations were generated for technical debt?",
]

TEXT_SUFFIXES = {
    ".py",
    ".java",
    ".js",
    ".ts",
    ".tsx",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".xml",
    ".md",
    ".gradle",
    ".kts",
    ".properties",
}


def _build_manifest(root: Path, *, key: str, limit: int = 50) -> RepositoryManifest:
    entries: list[RepositoryFileEntry] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if any(part.startswith(".") for part in Path(rel).parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        data = path.read_bytes()
        if len(data) > 120_000:
            continue
        entries.append(
            RepositoryFileEntry(
                path=RepositoryPath(rel),
                file_kind=RepositoryFileKind.SOURCE,
                size_bytes=len(data),
                fingerprint=hash_bytes(data, algorithm=HashAlgorithm.SHA256),
            )
        )
        if len(entries) >= limit:
            break
    return RepositoryManifest(
        identity=RepositoryIdentity(
            repository_key=key.replace("/", "-").replace(" ", "-")[:48] or "repo",
            source_type=RepositorySourceType.LOCAL,
            display_name=key,
        ),
        revision=RepositoryRevision(
            revision_id="working-tree",
            revision_type=RepositoryRevisionType.WORKING_TREE,
            branch="main",
        ),
        files=tuple(entries),
    )


def _finding(path: str) -> Finding:
    return Finding.create(
        rule_id="DOGFOOD-55",
        title="Dogfood finding",
        description="Synthetic finding for retrieval dogfood",
        severity=FindingSeverity.HIGH,
        category=FindingCategory.SECURITY,
        evidence=[
            FindingEvidence(
                evidence_type="file",
                source_id=path,
                path=path,
                excerpt="sample",
            )
        ],
        metadata={"confidence": "high"},
        subject_keys=[path],
    )


def _make_synthetic(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "architecture.md").write_text(
        "# Architecture\nRepository architecture is defined in this document.\n",
        encoding="utf-8",
    )
    (path / "AuthService.java").write_text(
        "public class AuthService { void authenticate() {} }\n",
        encoding="utf-8",
    )
    (path / "cloud.yml").write_text("aws:\n  region: us-east-1\n", encoding="utf-8")


def _index(root: Path, *, label: str, store, provider, dimension: int):
    manifest = _build_manifest(root, key=label)
    reader = LocalFilesystemContentReader(root)
    sample = str(manifest.files[0].path) if manifest.files else "README.md"
    corpus = build_knowledge_corpus(
        KnowledgeProjectionRequest(
            context=ProjectionContext(
                tenant_id="dogfood",
                repository_id=f"repo-{label}",
                scan_id=f"scan-{label}",
                branch="main",
                commit_sha="working-tree",
            ),
            repository_root=root,
            manifest=manifest,
            content_reader=reader,
            findings=(_finding(sample),),
            assessment_sections={},
            report_sections={},
        ),
        projection=KnowledgeProjectionSettings(enabled=True, include_report_sections=False),
        chunking=KnowledgeChunkingSettings(enabled=True),
    )
    indexer = KnowledgeIndexer(
        embedding_provider=provider,
        vector_store=store,
        embedding_settings=KnowledgeEmbeddingSettings(
            enabled=True, provider="deterministic", dimension=dimension
        ),
        indexing_settings=KnowledgeIndexingSettings(enabled=True),
    )
    scope = IndexScope(
        tenant_id="dogfood",
        repository_id=f"repo-{label}",
        scan_id=f"scan-{label}",
    )
    indexer.index(KnowledgeIndexRequest(corpus=corpus, scope=scope))
    return corpus


def _retrieve_all(label: str, store, provider, dimension: int, out_dir: Path) -> list[dict]:
    retriever = RepositoryRetriever(
        embedding_provider=provider,
        vector_store=store,
        retrieval_settings=KnowledgeRetrievalSettings(enabled=True),
        embedding_settings=KnowledgeEmbeddingSettings(
            enabled=True, provider="deterministic", dimension=dimension
        ),
    )
    rows: list[dict] = []
    for query in QUERIES:
        first = retriever.retrieve(
            RetrievalRequest(
                query=query,
                scope=RetrievalScope(
                    tenant_id="dogfood",
                    repository_id=f"repo-{label}",
                    scan_id=f"scan-{label}",
                ),
                top_k=5,
                candidate_limit=20,
            )
        )
        second = retriever.retrieve(
            RetrievalRequest(
                query=query,
                scope=RetrievalScope(
                    tenant_id="dogfood",
                    repository_id=f"repo-{label}",
                    scan_id=f"scan-{label}",
                ),
                top_k=5,
                candidate_limit=20,
            )
        )
        write_retrieval_result_artifact(
            first,
            out_dir / label,
            enabled=True,
            filename=f"{hash(query) & 0xFFFF:04x}.json",
            include_content=False,
        )
        rows.append(
            {
                "query": query,
                "status": first.status.value,
                "final_hit_count": first.coverage.final_hit_count,
                "citation_labels": list(first.context.citation_labels),
                "source_types": list(first.coverage.source_types),
                "files": list(first.coverage.files)[:10],
                "findings": list(first.coverage.findings),
                "deterministic": first.fingerprint == second.fingerprint,
            }
        )
    return rows


def main() -> int:
    out_dir = ROOT / "reports" / "dogfood-phase-5-5"
    out_dir.mkdir(parents=True, exist_ok=True)
    dimension = 64
    synthetic = out_dir / "synthetic-fixture"
    _make_synthetic(synthetic)
    targets = [
        ("synthetic-multi-lang", synthetic),
        ("codestrata", ROOT),
        ("spring-petclinic", ROOT / ".aimf" / "workspace" / "spring-petclinic"),
    ]
    summary: list[dict] = []
    for label, root in targets:
        if not root.is_dir():
            summary.append({"label": label, "skipped": True, "reason": f"missing {root}"})
            continue
        provider = DeterministicEmbeddingProvider(dimension=dimension)
        memory = InMemoryVectorStore()
        _index(root, label=label, store=memory, provider=provider, dimension=dimension)
        rows = _retrieve_all(label, memory, provider, dimension, out_dir)
        entry: dict = {"label": label, "provider": "memory", "queries": rows}
        if label == "codestrata":
            pg_url = (
                os.environ.get("CODESTRATA_DATABASE_URL", "").strip()
                or os.environ.get("AIMF_PGVECTOR_URL", "").strip()
            )
            if pg_url:
                from aimf.infrastructure.vector_store.pgvector import PgVectorStore

                with PgVectorStore(
                    connection_string=pg_url,
                    schema="codestrata_dogfood_55",
                    dimension=dimension,
                    hnsw=True,
                ) as pg:
                    pg.delete_scope(
                        IndexScope(
                            tenant_id="dogfood",
                            repository_id=f"repo-{label}",
                            scan_id=f"scan-{label}",
                        )
                    )
                    _index(root, label=label, store=pg, provider=provider, dimension=dimension)
                    pg_rows = _retrieve_all(label, pg, provider, dimension, out_dir)
                    entry["pgvector_queries"] = pg_rows
                    entry["memory_pg_hit_counts_match"] = [
                        m["final_hit_count"] == p["final_hit_count"]
                        for m, p in zip(rows, pg_rows, strict=True)
                    ]
            else:
                entry["pgvector"] = "skipped (no CODESTRATA_DATABASE_URL)"
        summary.append(entry)
        print(json.dumps({"label": label, "query_count": len(rows)}, sort_keys=True))

    (out_dir / "dogfood-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
