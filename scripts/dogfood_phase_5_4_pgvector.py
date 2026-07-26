"""Dogfood Phase 5.4 / 5.4.1 — index CodeStrata corpus into PostgreSQL + pgvector.

Compares vector counts and search ordering against InMemoryVectorStore using
DeterministicEmbeddingProvider.

Requires CODESTRATA_DATABASE_URL (or deprecated AIMF_PGVECTOR_URL).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aimf.application.knowledge.indexing import (  # noqa: E402
    KnowledgeIndexer,
    KnowledgeIndexRequest,
    write_knowledge_index_artifact,
)
from aimf.application.knowledge.projection import (  # noqa: E402
    KnowledgeProjectionRequest,
    ProjectionContext,
    build_knowledge_corpus,
)
from aimf.config.settings import (  # noqa: E402
    KnowledgeChunkingSettings,
    KnowledgeEmbeddingSettings,
    KnowledgeIndexingSettings,
    KnowledgeProjectionSettings,
)
from aimf.domain.findings.enums import FindingCategory, FindingSeverity  # noqa: E402
from aimf.domain.findings.models import Finding, FindingEvidence  # noqa: E402
from aimf.domain.knowledge.vector import IndexScope, VectorFilter, VectorQuery  # noqa: E402
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
from aimf.infrastructure.vector_store.pgvector import PgVectorStore  # noqa: E402
from aimf.services.inventory.content_reader import LocalFilesystemContentReader  # noqa: E402

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


def _build_manifest(root: Path, *, key: str, limit: int = 60) -> RepositoryManifest:
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


def _sample_finding(path: str) -> Finding:
    return Finding.create(
        rule_id="DOGFOOD-54",
        title="Dogfood finding",
        description="Synthetic finding for pgvector dogfood",
        severity=FindingSeverity.MEDIUM,
        category=FindingCategory.ARCHITECTURE,
        evidence=[
            FindingEvidence(
                evidence_type="file",
                source_id=path,
                path=path,
                excerpt="sample",
            )
        ],
        metadata={"confidence": "medium"},
        subject_keys=[path],
    )


def _project(root: Path, *, label: str):
    manifest = _build_manifest(root, key=label)
    reader = LocalFilesystemContentReader(root)
    sample = str(manifest.files[0].path) if manifest.files else "README.md"
    return build_knowledge_corpus(
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
            findings=(_sample_finding(sample),),
            assessment_sections={},
            report_sections={},
        ),
        projection=KnowledgeProjectionSettings(enabled=True, include_report_sections=False),
        chunking=KnowledgeChunkingSettings(enabled=True),
    )


def _index(corpus, store, *, label: str, dimension: int = 64):
    provider = DeterministicEmbeddingProvider(dimension=dimension)
    indexer = KnowledgeIndexer(
        embedding_provider=provider,
        vector_store=store,
        embedding_settings=KnowledgeEmbeddingSettings(
            enabled=True,
            provider="deterministic",
            dimension=dimension,
            batch_size=16,
        ),
        indexing_settings=KnowledgeIndexingSettings(
            enabled=True,
            delete_stale_records=True,
            write_manifest=True,
        ),
    )
    scope = IndexScope(
        tenant_id="dogfood",
        repository_id=f"repo-{label}",
        scan_id=f"scan-{label}",
    )
    result = indexer.index(KnowledgeIndexRequest(corpus=corpus, scope=scope))
    query = provider.embed_text(corpus.chunks[0].content if corpus.chunks else "x")
    hits = store.search(
        VectorQuery(
            embedding=query.embedding,
            top_k=5,
            filter=VectorFilter(
                tenant_id="dogfood",
                repository_id=f"repo-{label}",
                scan_id=f"scan-{label}",
            ),
        )
    )
    return result, hits, provider


def main() -> int:
    pg_url = (
        os.environ.get("CODESTRATA_DATABASE_URL", "").strip()
        or os.environ.get("AIMF_PGVECTOR_URL", "").strip()
    )
    if not pg_url:
        print(
            "CODESTRATA_DATABASE_URL is required "
            "(deprecated alias: AIMF_PGVECTOR_URL)",
            file=sys.stderr,
        )
        return 2

    out_dir = ROOT / "reports" / "dogfood-phase-5-4"
    out_dir.mkdir(parents=True, exist_ok=True)
    label = "codestrata"
    corpus = _project(ROOT, label=label)
    dimension = 64

    memory = InMemoryVectorStore()
    mem_result, mem_hits, _ = _index(corpus, memory, label=label, dimension=dimension)

    with PgVectorStore(
        connection_string=pg_url,
        schema="codestrata_dogfood_54",
        dimension=dimension,
        hnsw=True,
        migrate=True,
    ) as pg:
        # Clear prior dogfood scope for deterministic reruns.
        pg.delete_scope(
            IndexScope(
                tenant_id="dogfood",
                repository_id=f"repo-{label}",
                scan_id=f"scan-{label}",
            )
        )
        pg_result, pg_hits, _ = _index(corpus, pg, label=label, dimension=dimension)
        health = pg.health()
        write_knowledge_index_artifact(pg_result, out_dir / label, enabled=True)

        mem_ids = [item.record_id for item in mem_hits]
        pg_ids = [item.record_id for item in pg_hits]
        summary = {
            "label": label,
            "document_count": corpus.coverage.document_count,
            "chunk_count": corpus.coverage.chunk_count,
            "memory_vector_count": mem_result.manifest.coverage.vector_count,
            "pgvector_vector_count": pg_result.manifest.coverage.vector_count,
            "counts_match": mem_result.manifest.coverage.vector_count
            == pg_result.manifest.coverage.vector_count
            == len(memory)
            == len(pg),
            "memory_search_ids": mem_ids,
            "pgvector_search_ids": pg_ids,
            "search_ids_match": mem_ids == pg_ids,
            "health": health.model_dump(mode="json"),
            "capabilities": pg.capabilities().model_dump(mode="json"),
            "hnsw_index": health.detail.get("hnsw_index"),
        }
        (out_dir / "dogfood-summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(summary, sort_keys=True))
        return 0 if summary["counts_match"] and summary["search_ids_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
