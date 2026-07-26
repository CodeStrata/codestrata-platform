"""Community export must not include Platform RAG/KG commercial runtime."""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
ENGINE_SRC = REPO_ROOT / "engine" / "src" / "codestrata"


def test_engine_source_has_no_enterprise_or_rag_impl_packages() -> None:
    assert not (ENGINE_SRC / "application" / "enterprise").exists()
    assert not (ENGINE_SRC / "domain" / "enterprise").exists()
    assert not (ENGINE_SRC / "infrastructure" / "enterprise").exists()
    assert not (ENGINE_SRC / "infrastructure" / "embedding").exists()
    assert not (ENGINE_SRC / "infrastructure" / "vector_store").exists()
    assert not (ENGINE_SRC / "application" / "knowledge" / "projection").exists()
    assert not (ENGINE_SRC / "application" / "knowledge" / "indexing").exists()
    assert not (ENGINE_SRC / "application" / "knowledge" / "retrieval").exists()
    assert not (ENGINE_SRC / "application" / "knowledge" / "answering").exists()


def test_manifest_forbids_platform_and_keeps_extension_hook() -> None:
    manifest = yaml.safe_load(
        (REPO_ROOT / "public-export-manifest.yaml").read_text(encoding="utf-8")
    )
    engine = next(item for item in manifest["exports"] if item["name"] == "codestrata-engine")
    forbid = "\n".join(engine["validation"]["forbid_globs"])
    assert "platform/**" in forbid
    required = engine["validation"]["require_files"]
    assert "src/codestrata/extensions/__init__.py" in required
    assert "SECURITY.md" in required
    blob = (REPO_ROOT / "public-export-manifest.yaml").read_text(encoding="utf-8")
    assert "university" not in blob.lower()


def test_extension_hook_documented_in_export_requirements() -> None:
    manifest = yaml.safe_load(
        (REPO_ROOT / "public-export-manifest.yaml").read_text(encoding="utf-8")
    )
    engine = next(item for item in manifest["exports"] if item["name"] == "codestrata-engine")
    required = engine["validation"]["require_files"]
    assert "src/codestrata/extensions/__init__.py" in required
    assert "SECURITY.md" in required
