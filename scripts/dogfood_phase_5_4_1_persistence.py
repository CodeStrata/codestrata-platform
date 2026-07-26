"""Dogfood Phase 5.4.1 — persistence across process restarts.

Uses CODESTRATA_DATABASE_URL (Docker Compose or any reachable PostgreSQL).
Validates vector survival after disposing PgVectorStore and opening a new one,
plus scoped deletion. Optional Docker stop/start when compose is available.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine" / "src"))

from codestrata.security.database_url import redact_database_url  # noqa: E402
from codestrata_platform.rag.domain import IndexScope, VectorQuery, VectorRecord  # noqa: E402
from codestrata_platform.rag.vector_store.pgvector import PgVectorStore  # noqa: E402


def _url() -> str:
    return (
        os.environ.get("CODESTRATA_DATABASE_URL", "").strip()
        or os.environ.get("CODESTRATA_PGVECTOR_URL", "").strip()
    )


def _record(entity_id: str, *, scan_id: str) -> VectorRecord:
    return VectorRecord.create(
        entity_id=entity_id,
        embedding=[1.0, 0.0, 0.0, 0.0],
        metadata={
            "tenant_id": "dogfood-541",
            "repository_id": "repo-persist",
            "scan_id": scan_id,
            "document_id": f"kd:{entity_id}",
            "chunk_id": f"kc:{entity_id}",
        },
    )


def _docker_compose(*args: str) -> bool:
    docker = shutil.which("docker") or (
        "/Applications/Docker.app/Contents/Resources/bin/docker"
        if Path("/Applications/Docker.app/Contents/Resources/bin/docker").exists()
        else None
    )
    if not docker:
        return False
    compose = ROOT / "docker-compose.yml"
    if not compose.is_file():
        return False
    result = subprocess.run(
        [docker, "compose", "-f", str(compose), *args],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        timeout=180,
    )
    return result.returncode == 0


def main() -> int:
    url = _url()
    if not url:
        print("CODESTRATA_DATABASE_URL is required", file=sys.stderr)
        return 2

    out_dir = ROOT / "reports" / "dogfood-phase-5-4-1"
    out_dir.mkdir(parents=True, exist_ok=True)
    schema = "codestrata_dogfood_541"
    scope = IndexScope(
        tenant_id="dogfood-541",
        repository_id="repo-persist",
        scan_id="scan-persist",
    )

    with PgVectorStore(
        connection_string=url, schema=schema, dimension=4, hnsw=True
    ) as store:
        store.delete_scope(scope)
        store.upsert([_record("a", scan_id="scan-persist"), _record("b", scan_id="scan-persist")])
        count_1 = len(store)
        health_1 = store.health().model_dump(mode="json")

    with PgVectorStore(
        connection_string=url, schema=schema, dimension=4, hnsw=True
    ) as store:
        count_2 = len(store)
        process_persist = count_2 == count_1 == 2

    docker_restart_persist: bool | None = None
    docker_attempted = False
    if os.environ.get("CODESTRATA_DOGFOOD_DOCKER_RESTART", "").strip() == "1":
        docker_attempted = True
        if _docker_compose("stop", "postgres") and _docker_compose("up", "-d", "postgres"):
            time.sleep(5)
            try:
                with PgVectorStore(
                    connection_string=url, schema=schema, dimension=4, hnsw=True
                ) as store:
                    docker_restart_persist = len(store) == count_1
            except Exception as exc:  # noqa: BLE001
                docker_restart_persist = False
                print(f"docker restart check failed: {exc}", file=sys.stderr)
        else:
            docker_restart_persist = False

    with PgVectorStore(
        connection_string=url, schema=schema, dimension=4, hnsw=True
    ) as store:
        deleted = store.delete_scope(scope)
        remaining = len(store.search(VectorQuery(embedding=(1.0, 0.0, 0.0, 0.0), top_k=10)))

    summary = {
        "endpoint": redact_database_url(url),
        "schema": schema,
        "count_after_upsert": count_1,
        "count_after_new_process": count_2,
        "process_persistence_ok": process_persist,
        "scoped_delete_count": deleted,
        "remaining_after_delete": remaining,
        "scoped_delete_ok": deleted == 2 and remaining == 0,
        "health": health_1,
        "docker_restart_attempted": docker_attempted,
        "docker_restart_persist": docker_restart_persist,
    }
    (out_dir / "persistence-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))
    ok = process_persist and summary["scoped_delete_ok"]
    if docker_attempted and docker_restart_persist is False:
        ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
