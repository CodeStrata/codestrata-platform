"""Configuration defaults for Repository Knowledge Layer (Phase 5.1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from aimf.config.settings import KnowledgeSettings, KnowledgeVectorStoreSettings, load_settings
from aimf.infrastructure.vector_store import create_vector_store


def test_knowledge_defaults_include_repository_layer_flags() -> None:
    settings = KnowledgeSettings()
    assert settings.directory == Path(".aimf/knowledge")
    assert settings.enabled is False
    assert settings.vector_store.provider == "memory"
    assert settings.projection.enabled is False
    assert settings.chunking.enabled is False
    assert settings.chunking.max_characters == 4000
    assert settings.chunking.overlap_characters == 400
    assert settings.chunking.preserve_logical_units is True
    assert settings.projection.include_findings is True
    assert settings.embedding.enabled is False
    assert settings.embedding.provider == "deterministic"
    assert settings.embedding.dimension == 384
    assert settings.indexing.enabled is False
    assert settings.indexing.delete_stale_records is True
    assert settings.retrieval.enabled is False
    assert settings.retrieval.top_k == 10
    assert settings.retrieval.candidate_limit == 30


def test_load_settings_knowledge_defaults(tmp_path: Path) -> None:
    config_file = tmp_path / "aimf.toml"
    config_file.write_text(
        """
        [repository]
        path = "examples/sample-js-app"
        """,
        encoding="utf-8",
    )
    settings = load_settings(config_file)
    assert settings.knowledge.enabled is False
    assert settings.knowledge.vector_store.provider == "memory"
    assert settings.knowledge.directory == Path(".aimf/knowledge")


def test_load_settings_knowledge_vector_store_section(tmp_path: Path) -> None:
    config_file = tmp_path / "aimf.toml"
    config_file.write_text(
        """
        [repository]
        path = "examples/sample-js-app"

        [knowledge]
        directory = ".aimf/custom-knowledge"
        enabled = true

        [knowledge.vector_store]
        provider = "memory"
        """,
        encoding="utf-8",
    )
    settings = load_settings(config_file)
    assert settings.knowledge.enabled is True
    assert settings.knowledge.directory == Path(".aimf/custom-knowledge")
    assert settings.knowledge.vector_store.provider == "memory"


def test_load_settings_knowledge_embedding_and_indexing(tmp_path: Path) -> None:
    config_file = tmp_path / "aimf.toml"
    config_file.write_text(
        """
        [repository]
        path = "examples/sample-js-app"

        [knowledge.embedding]
        enabled = true
        provider = "deterministic"
        dimension = 64
        batch_size = 8

        [knowledge.indexing]
        enabled = true
        delete_stale_records = false
        write_manifest = true
        """,
        encoding="utf-8",
    )
    settings = load_settings(config_file)
    assert settings.knowledge.embedding.enabled is True
    assert settings.knowledge.embedding.dimension == 64
    assert settings.knowledge.embedding.batch_size == 8
    assert settings.knowledge.indexing.enabled is True
    assert settings.knowledge.indexing.delete_stale_records is False
    assert settings.knowledge.indexing.write_manifest is True
    assert settings.knowledge.vector_store.provider == "memory"


def test_load_settings_knowledge_projection_and_chunking(tmp_path: Path) -> None:
    config_file = tmp_path / "aimf.toml"
    config_file.write_text(
        """
        [repository]
        path = "examples/sample-js-app"

        [knowledge.projection]
        enabled = true
        include_findings = false
        write_corpus_artifact = true

        [knowledge.chunking]
        enabled = true
        max_characters = 2000
        overlap_characters = 200
        preserve_logical_units = false
        """,
        encoding="utf-8",
    )
    settings = load_settings(config_file)
    assert settings.knowledge.projection.enabled is True
    assert settings.knowledge.projection.include_findings is False
    assert settings.knowledge.projection.write_corpus_artifact is True
    assert settings.knowledge.chunking.enabled is True
    assert settings.knowledge.chunking.max_characters == 2000
    assert settings.knowledge.chunking.overlap_characters == 200
    assert settings.knowledge.chunking.preserve_logical_units is False
    assert settings.knowledge.vector_store.provider == "memory"


def test_pgvector_provider_requires_connection_string(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("AIMF_PGVECTOR_URL", raising=False)
    monkeypatch.delenv("CODESTRATA_DATABASE_URL", raising=False)
    monkeypatch.delenv("CODESTRATA_VECTOR_STORE_PROVIDER", raising=False)
    config_file = tmp_path / "aimf.toml"
    config_file.write_text(
        """
        [repository]
        path = "examples/sample-js-app"

        [knowledge.vector_store]
        provider = "pgvector"
        schema = "codestrata"
        hnsw = true
        """,
        encoding="utf-8",
    )
    settings = load_settings(config_file)
    assert settings.knowledge.vector_store.provider == "pgvector"
    assert settings.knowledge.vector_store.schema_name == "codestrata"
    assert settings.knowledge.vector_store.hnsw is True
    with pytest.raises(ValueError, match="CODESTRATA_DATABASE_URL"):
        create_vector_store(settings.knowledge)


def test_invalid_vector_store_provider_rejected() -> None:
    with pytest.raises(ValueError, match="knowledge.vector_store.provider"):
        KnowledgeVectorStoreSettings(provider="pinecone")
