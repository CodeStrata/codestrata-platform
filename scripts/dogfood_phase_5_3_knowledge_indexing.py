"""Dogfood Phase 5.3 embedding + indexing on projected corpora.

Builds corpora (Phase 5.2 style), indexes with DeterministicEmbeddingProvider
into InMemoryVectorStore, and writes manifests under reports/dogfood-phase-5-3/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aimf.application.knowledge.indexing import (  # noqa: E402
    KnowledgeIndexRequest,
    KnowledgeIndexer,
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
        rule_id="DOGFOOD-001",
        title="Dogfood finding",
        description="Synthetic finding for indexing dogfood",
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


def _make_synthetic(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "app.py").write_text(
        "import sys\n\nclass Service:\n    def run(self):\n        return 1\n",
        encoding="utf-8",
    )
    (path / "App.java").write_text(
        "package demo;\npublic class App { public void start() {} }\n",
        encoding="utf-8",
    )
    (path / "index.js").write_text("export const n = 1;\n", encoding="utf-8")


def _project_and_index(root: Path, *, label: str, out_dir: Path) -> dict[str, object]:
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
            findings=(_sample_finding(sample),),
            assessment_sections={},
            report_sections={},
        ),
        projection=KnowledgeProjectionSettings(enabled=True, include_report_sections=False),
        chunking=KnowledgeChunkingSettings(enabled=True),
    )

    store = InMemoryVectorStore()
    provider = DeterministicEmbeddingProvider(dimension=64)
    indexer = KnowledgeIndexer(
        embedding_provider=provider,
        vector_store=store,
        embedding_settings=KnowledgeEmbeddingSettings(
            enabled=True,
            provider="deterministic",
            dimension=64,
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
    first = indexer.index(KnowledgeIndexRequest(corpus=corpus, scope=scope))
    second = indexer.index(
        KnowledgeIndexRequest(corpus=corpus, scope=scope, prior_manifest=first.manifest)
    )

    target = out_dir / label
    target.mkdir(parents=True, exist_ok=True)
    write_knowledge_index_artifact(first, target, enabled=True)
    query = provider.embed_text(corpus.chunks[0].content if corpus.chunks else "x")
    hits = store.search(
        VectorQuery(
            embedding=query.embedding,
            top_k=3,
            filter=VectorFilter(
                tenant_id="dogfood",
                repository_id=f"repo-{label}",
                scan_id=f"scan-{label}",
            ),
        )
    )
    summary = {
        "label": label,
        "document_count": corpus.coverage.document_count,
        "chunk_count": corpus.coverage.chunk_count,
        "vector_count": first.manifest.coverage.vector_count,
        "added": first.manifest.coverage.added,
        "updated": first.manifest.coverage.updated,
        "unchanged_second_pass": second.manifest.coverage.unchanged,
        "removed": first.manifest.coverage.removed,
        "status": first.status.value,
        "second_status": second.status.value,
        "search_hits": len(hits),
        "deterministic_second_pass": second.manifest.coverage.unchanged
        == first.manifest.coverage.vector_count,
        "store_size": len(store),
        "manifest_id": first.manifest.manifest_id,
    }
    (target / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    out_dir = ROOT / "reports" / "dogfood-phase-5-3"
    out_dir.mkdir(parents=True, exist_ok=True)
    synthetic = out_dir / "synthetic-fixture"
    _make_synthetic(synthetic)
    targets = [
        ("synthetic-multi-lang", synthetic),
        ("codestrata", ROOT),
        ("spring-petclinic", ROOT / ".aimf" / "workspace" / "spring-petclinic"),
    ]
    summaries = []
    for label, root in targets:
        if not root.is_dir():
            summaries.append({"label": label, "skipped": True, "reason": f"missing {root}"})
            continue
        summaries.append(_project_and_index(root, label=label, out_dir=out_dir))
    (out_dir / "dogfood-summary.json").write_text(
        json.dumps(summaries, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    for item in summaries:
        print(json.dumps(item, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
