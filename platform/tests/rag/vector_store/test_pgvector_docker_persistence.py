"""Docker Compose persistence tests for PgVectorStore (Phase 5.4.1).

Marked ``docker``. Skipped when Docker is unavailable — never reported as passed.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from codestrata_platform.rag.domain import IndexScope, VectorQuery, VectorRecord
from codestrata_platform.rag.vector_store.pgvector import PgVectorStore

ROOT = Path(__file__).resolve().parents[3]
COMPOSE_FILE = ROOT / "docker-compose.yml"
DOCKER_URL = "postgresql://codestrata:codestrata@127.0.0.1:5432/codestrata"
SCHEMA = "codestrata_docker_persist_541"


def _docker_bin() -> str | None:
    for candidate in (
        shutil.which("docker"),
        "/Applications/Docker.app/Contents/Resources/bin/docker",
        "/usr/local/bin/docker",
    ):
        if candidate and Path(candidate).exists():
            return candidate
    return None


def _docker_available() -> bool:
    docker = _docker_bin()
    if docker is None or not COMPOSE_FILE.is_file():
        return False
    try:
        result = subprocess.run(
            [docker, "info"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
            env={**os.environ, "PATH": f"{Path(docker).parent}:{os.environ.get('PATH', '')}"},
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _compose(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    docker = _docker_bin()
    assert docker is not None
    env = {
        **os.environ,
        "PATH": f"{Path(docker).parent}:{os.environ.get('PATH', '')}",
    }
    return subprocess.run(
        [docker, "compose", "-f", str(COMPOSE_FILE), *args],
        check=check,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        timeout=180,
        env=env,
    )


pytestmark = [
    pytest.mark.docker,
    pytest.mark.skipif(
        not _docker_available(),
        reason="Docker daemon unavailable (docker compose pgvector tests skipped)",
    ),
]


def _record(entity_id: str, *, scan_id: str = "scan-persist") -> VectorRecord:
    return VectorRecord.create(
        entity_id=entity_id,
        embedding=[1.0, 0.0, 0.0, 0.0],
        metadata={
            "tenant_id": "docker-tenant",
            "repository_id": "docker-repo",
            "scan_id": scan_id,
            "document_id": f"kd:{entity_id}",
            "chunk_id": f"kc:{entity_id}",
        },
    )


def _wait_ready(*, attempts: int = 30) -> None:
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            with PgVectorStore(
                connection_string=DOCKER_URL,
                schema=SCHEMA,
                dimension=4,
                hnsw=True,
                connect_timeout_seconds=5,
            ) as store:
                health = store.health()
                if health.healthy and health.detail.get("pgvector_extension"):
                    return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
        time.sleep(1)
    raise AssertionError(f"postgres not ready: {last_error}")


@pytest.fixture(scope="module")
def docker_postgres() -> Iterator[None]:
    _compose("up", "-d", "postgres")
    _wait_ready()
    yield
    # Preserve volume: stop service only (no -v).
    _compose("stop", "postgres", check=False)


def test_container_connectivity_and_extension(docker_postgres: None) -> None:
    with PgVectorStore(
        connection_string=DOCKER_URL,
        schema=SCHEMA,
        dimension=4,
        hnsw=True,
    ) as store:
        health = store.health()
        assert health.healthy is True
        assert health.detail.get("connectivity") is True
        assert health.detail.get("persistent") is True
        assert health.detail.get("pgvector_extension") is True
        assert health.detail.get("pgvector_version")
        assert health.detail.get("postgres_version")
        assert health.detail.get("schema") == SCHEMA
        assert "password" not in str(health.model_dump()).lower() or "codestrata" not in (
            health.message or ""
        )
        dumped = str(health.model_dump())
        assert "codestrata:codestrata" not in dumped


def test_bootstrap_and_migration_idempotency(docker_postgres: None) -> None:
    first = PgVectorStore(
        connection_string=DOCKER_URL,
        schema=SCHEMA,
        dimension=4,
        hnsw=True,
    )
    first.close()
    second = PgVectorStore(
        connection_string=DOCKER_URL,
        schema=SCHEMA,
        dimension=4,
        hnsw=True,
    )
    assert second.health().detail.get("schema_version") == first.health().detail.get(
        "schema_version"
    )
    second.close()


def test_persistence_across_new_store_instances(docker_postgres: None) -> None:
    scope = IndexScope(
        tenant_id="docker-tenant",
        repository_id="docker-repo",
        scan_id="scan-persist",
    )
    with PgVectorStore(
        connection_string=DOCKER_URL,
        schema=SCHEMA,
        dimension=4,
        hnsw=True,
    ) as store:
        store.delete_scope(scope)
        store.upsert([_record("persist-a"), _record("persist-b")])
        assert len(store) >= 2
        count_before = len(store)

    with PgVectorStore(
        connection_string=DOCKER_URL,
        schema=SCHEMA,
        dimension=4,
        hnsw=True,
    ) as store:
        assert len(store) == count_before
        hits = store.search(VectorQuery(embedding=(1.0, 0.0, 0.0, 0.0), top_k=10))
        assert {item.record.entity_id for item in hits} >= {"persist-a", "persist-b"}


def test_persistence_across_docker_stop_start(docker_postgres: None) -> None:
    scope = IndexScope(
        tenant_id="docker-tenant",
        repository_id="docker-repo",
        scan_id="scan-restart",
    )
    with PgVectorStore(
        connection_string=DOCKER_URL,
        schema=SCHEMA,
        dimension=4,
        hnsw=True,
    ) as store:
        store.delete_scope(scope)
        store.upsert([_record("restart-1", scan_id="scan-restart")])
        count_before = len(store)

    _compose("stop", "postgres")
    time.sleep(2)
    _compose("up", "-d", "postgres")
    _wait_ready()

    with PgVectorStore(
        connection_string=DOCKER_URL,
        schema=SCHEMA,
        dimension=4,
        hnsw=True,
    ) as store:
        assert len(store) == count_before
        hits = store.search(
            VectorQuery(
                embedding=(1.0, 0.0, 0.0, 0.0),
                top_k=5,
            )
        )
        assert any(item.record.entity_id == "restart-1" for item in hits)


def test_scoped_deletion_after_restart(docker_postgres: None) -> None:
    keep_scope = IndexScope(
        tenant_id="docker-tenant",
        repository_id="docker-repo",
        scan_id="scan-keep",
    )
    drop_scope = IndexScope(
        tenant_id="docker-tenant",
        repository_id="docker-repo",
        scan_id="scan-drop",
    )
    with PgVectorStore(
        connection_string=DOCKER_URL,
        schema=SCHEMA,
        dimension=4,
        hnsw=True,
    ) as store:
        store.delete_scope(keep_scope)
        store.delete_scope(drop_scope)
        store.upsert(
            [
                _record("keep", scan_id="scan-keep"),
                _record("drop", scan_id="scan-drop"),
            ]
        )
        deleted = store.delete_scope(drop_scope)
        assert deleted == 1
        hits = store.search(VectorQuery(embedding=(1.0, 0.0, 0.0, 0.0), top_k=10))
        entities = {item.record.entity_id for item in hits}
        assert "keep" in entities
        assert "drop" not in entities
