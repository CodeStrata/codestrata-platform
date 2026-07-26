"""Dogfood Phase 5.2 knowledge projection/chunking on local repositories.

Writes summaries under ``reports/dogfood-phase-5-2/`` (gitignored).
Does not generate embeddings or write to a vector store.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aimf.application.knowledge.projection import (  # noqa: E402
    KnowledgeProjectionRequest,
    ProjectionContext,
    build_knowledge_corpus,
    write_knowledge_corpus_artifact,
)
from aimf.config.settings import KnowledgeChunkingSettings, KnowledgeProjectionSettings
from aimf.domain.findings.enums import FindingCategory, FindingSeverity
from aimf.domain.findings.models import Finding, FindingEvidence
from aimf.domain.repository.enums import (  # noqa: E402
    HashAlgorithm,
    RepositoryFileKind,
    RepositoryRevisionType,
    RepositorySourceType,
)
from aimf.domain.repository.files import RepositoryFileEntry
from aimf.domain.repository.fingerprints import hash_bytes
from aimf.domain.repository.identities import RepositoryIdentity, RepositoryRevision
from aimf.domain.repository.manifests import RepositoryManifest
from aimf.domain.repository.paths import RepositoryPath
from aimf.services.artifact_serialization import dumps_stable_json
from aimf.services.inventory.content_reader import LocalFilesystemContentReader

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


def _build_manifest(root: Path, *, key: str, limit: int = 80) -> RepositoryManifest:
    entries: list[RepositoryFileEntry] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if any(part.startswith(".") for part in Path(rel).parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name.lower() not in {
            "dockerfile",
            "makefile",
        }:
            continue
        data = path.read_bytes()
        if len(data) > 200_000:
            continue
        entries.append(
            RepositoryFileEntry(
                path=RepositoryPath(rel),
                file_kind=RepositoryFileKind.SOURCE,
                size_bytes=len(data),
                fingerprint=hash_bytes(data, algorithm=HashAlgorithm.SHA256),
                language=_language(path.suffix.lower()),
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


def _language(suffix: str) -> str | None:
    return {
        ".py": "python",
        ".java": "java",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".toml": "toml",
        ".xml": "xml",
        ".json": "json",
        ".md": "markdown",
        ".gradle": "groovy",
        ".kts": "kotlin",
    }.get(suffix)


def _sample_finding(path: str) -> Finding:
    return Finding.create(
        rule_id="DOGFOOD-001",
        title="Dogfood finding",
        description="Synthetic finding for projection dogfood",
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


def _project(root: Path, *, label: str, out_dir: Path) -> dict[str, object]:
    manifest = _build_manifest(root, key=label)
    reader = LocalFilesystemContentReader(root)
    sample_path = str(manifest.files[0].path) if manifest.files else "README.md"
    request = KnowledgeProjectionRequest(
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
        findings=(_sample_finding(sample_path),),
        recommendations=(),
        evidence_items=(),
        assessment_sections={
            "architecture": None,
            "security": type(
                "Sec",
                (),
                {
                    "status": "complete",
                    "assessment_id": f"{label}-security",
                    "section_id": "security",
                    "section_version": "1.2.0",
                    "finding_ids": ("f1",),
                    "synthesis": None,
                    "themes": (),
                    "conclusions": (),
                    "recommendations": (),
                    "limitations": (),
                    "coverage": None,
                    "execution_summary": None,
                    "security_pack_id": "security.core",
                },
            )(),
        },
        report_sections={},
    )
    projection = KnowledgeProjectionSettings(
        enabled=True,
        write_corpus_artifact=True,
        include_report_sections=False,
    )
    chunking = KnowledgeChunkingSettings(enabled=True)
    left = build_knowledge_corpus(request, projection=projection, chunking=chunking)
    right = build_knowledge_corpus(request, projection=projection, chunking=chunking)
    target = out_dir / label
    target.mkdir(parents=True, exist_ok=True)
    write_knowledge_corpus_artifact(left, target, enabled=True)
    summary = {
        "label": label,
        "root": str(root),
        "document_count": left.coverage.document_count,
        "chunk_count": left.coverage.chunk_count,
        "by_source_type": left.coverage.by_source_type,
        "corpus_id": left.corpus_id,
        "fingerprint": left.fingerprint,
        "deterministic": left.fingerprint == right.fingerprint
        and dumps_stable_json(left.model_dump(mode="json"))
        == dumps_stable_json(right.model_dump(mode="json")),
        "oversize_units": left.coverage.oversize_units,
        "fallback_chunks": left.coverage.fallback_chunks,
        "diagnostic_count": len(left.diagnostics),
    }
    (target / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def _make_synthetic(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "app.py").write_text(
        "import sys\n\nclass Service:\n    def run(self):\n        return 1\n\ndef main():\n    print(Service().run())\n",
        encoding="utf-8",
    )
    (path / "App.java").write_text(
        "package demo;\n\npublic class App {\n  public void start() {}\n}\n",
        encoding="utf-8",
    )
    (path / "index.js").write_text(
        "export function greet(name) {\n  return `hi ${name}`;\n}\n",
        encoding="utf-8",
    )
    (path / "config.toml").write_text("[app]\nname = \"synthetic\"\n", encoding="utf-8")


def main() -> int:
    out_dir = ROOT / "reports" / "dogfood-phase-5-2"
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
        summaries.append(_project(root, label=label, out_dir=out_dir))

    (out_dir / "dogfood-summary.json").write_text(
        json.dumps(summaries, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    for item in summaries:
        print(json.dumps(item, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
