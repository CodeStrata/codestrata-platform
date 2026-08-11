"""Configuration resolution and factory hardening (Phase 5.4.1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from codestrata.config.dotenv import apply_dotenv_file
from codestrata.config.settings import KnowledgeVectorStoreSettings, load_settings
from codestrata_platform.rag.vector_store import create_vector_store
from codestrata_platform.rag.vector_store.resolution import (
    DEPRECATED_ENV_DATABASE_URL,
    ENV_DATABASE_SCHEMA,
    ENV_DATABASE_URL,
    ENV_VECTOR_STORE_PROVIDER,
    VectorStoreConfigurationError,
    VectorStoreConnectivityError,
    resolve_database_url,
    resolve_vector_store_provider,
    resolve_vector_store_schema,
)


@pytest.fixture(autouse=True)
def _clear_vector_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        ENV_VECTOR_STORE_PROVIDER,
        ENV_DATABASE_URL,
        ENV_DATABASE_SCHEMA,
        DEPRECATED_ENV_DATABASE_URL,
    ):
        monkeypatch.delenv(key, raising=False)


def test_memory_is_default_provider() -> None:
    assert resolve_vector_store_provider(None) == "memory"
    assert create_vector_store().capabilities().provider_id == "memory"
    health = create_vector_store().health()
    assert health.healthy is True
    assert health.detail.get("persistent") is False


def test_environment_provider_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_VECTOR_STORE_PROVIDER, "pgvector")
    settings = KnowledgeVectorStoreSettings(provider="memory")
    assert resolve_vector_store_provider(settings) == "pgvector"


def test_environment_schema_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_DATABASE_SCHEMA, "tenant_alpha")
    settings = KnowledgeVectorStoreSettings(schema="codestrata")
    assert resolve_vector_store_schema(settings) == "tenant_alpha"


def test_codestrata_database_url_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        ENV_DATABASE_URL,
        "postgresql://user:secret@localhost:5432/codestrata",
    )
    url = resolve_database_url(KnowledgeVectorStoreSettings())
    assert url is not None
    assert "secret" in url  # raw resolution returns real URL for connecting


def test_deprecated_codestrata_pgvector_url_compatibility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        DEPRECATED_ENV_DATABASE_URL,
        "postgresql://user:old@localhost:5432/codestrata",
    )
    url = resolve_database_url(None)
    assert url is not None
    assert "old" in url


def test_canonical_url_wins_over_deprecated_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        ENV_DATABASE_URL,
        "postgresql://user:new@localhost:5432/codestrata",
    )
    monkeypatch.setenv(
        DEPRECATED_ENV_DATABASE_URL,
        "postgresql://user:old@localhost:5432/codestrata",
    )
    url = resolve_database_url(None)
    assert url is not None
    assert "new" in url
    assert "old" not in url


def test_missing_database_url_is_actionable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_VECTOR_STORE_PROVIDER, "pgvector")
    with pytest.raises(VectorStoreConfigurationError, match=ENV_DATABASE_URL) as exc:
        create_vector_store()
    assert "postgresql://user:secret" not in str(exc.value)


def test_missing_url_error_does_not_include_password(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(ENV_VECTOR_STORE_PROVIDER, "pgvector")
    with pytest.raises(VectorStoreConfigurationError) as exc:
        create_vector_store(
            KnowledgeVectorStoreSettings(provider="pgvector"),
        )
    text = str(exc.value)
    assert "password" not in text.lower() or "CODESTRATA_DATABASE_URL" in text


def test_unknown_provider_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_VECTOR_STORE_PROVIDER, "pinecone")
    with pytest.raises(VectorStoreConfigurationError, match="unsupported"):
        create_vector_store()


def test_invalid_schema_identifier(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_DATABASE_SCHEMA, "bad-schema!")
    with pytest.raises(VectorStoreConfigurationError, match="schema"):
        resolve_vector_store_schema(None)


def test_no_silent_fallback_to_memory_when_pgvector_unreachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(ENV_VECTOR_STORE_PROVIDER, "pgvector")
    monkeypatch.setenv(
        ENV_DATABASE_URL,
        "postgresql://codestrata:codestrata@127.0.0.1:1/codestrata",
    )
    with pytest.raises((VectorStoreConnectivityError, VectorStoreConfigurationError)):
        create_vector_store(dimension=4)
    # Must not return memory store
    with pytest.raises((VectorStoreConnectivityError, VectorStoreConfigurationError)):
        store = create_vector_store(dimension=4)
        assert store.capabilities().provider_id != "memory"


def test_connectivity_error_redacts_password(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_VECTOR_STORE_PROVIDER, "pgvector")
    monkeypatch.setenv(
        ENV_DATABASE_URL,
        "postgresql://codestrata:super-secret-pass@127.0.0.1:1/codestrata",
    )
    with pytest.raises(
        (VectorStoreConnectivityError, VectorStoreConfigurationError)
    ) as exc:
        create_vector_store(dimension=4)
    text = str(exc.value)
    assert "super-secret-pass" not in text
    assert "***" in text or "unreachable" in text.lower()


def test_dotenv_does_not_override_existing_os_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(ENV_VECTOR_STORE_PROVIDER, "memory")
    env_file = tmp_path / ".env"
    env_file.write_text(
        f"{ENV_VECTOR_STORE_PROVIDER}=pgvector\n",
        encoding="utf-8",
    )
    apply_dotenv_file(env_file, override=False)
    assert resolve_vector_store_provider(None) == "memory"


def test_toml_connection_string_deprecated_still_works_last(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = KnowledgeVectorStoreSettings(
        provider="pgvector",
        connection_string="postgresql://user:fromtoml@localhost:5432/db",
    )
    url = resolve_database_url(settings)
    assert url is not None
    assert "fromtoml" in url


def test_programmatic_url_used_when_env_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    url = resolve_database_url(
        None,
        programmatic_url="postgresql://user:prog@localhost:5432/db",
    )
    assert url is not None
    assert "prog" in url


def test_load_settings_vector_store_hardening_fields(tmp_path: Path) -> None:
    config_file = tmp_path / "codestrata.toml"
    config_file.write_text(
        """
        [repository]
        path = "test-fixtures/sample-js-app"

        [knowledge.vector_store]
        provider = "memory"
        connection_string_env = "CODESTRATA_DATABASE_URL"
        schema = "codestrata"
        hnsw = true
        connect_timeout_seconds = 15
        """,
        encoding="utf-8",
    )
    settings = load_settings(config_file)
    assert settings.knowledge.vector_store.provider == "memory"
    assert settings.knowledge.vector_store.connection_string_env == (
        "CODESTRATA_DATABASE_URL"
    )
    assert settings.knowledge.vector_store.connect_timeout_seconds == 15
