"""Ephemeral PostgreSQL helpers for Commercial Platform persistence tests.

Uses local Homebrew/initdb PostgreSQL when Docker Compose is unavailable.
Never falls back to SQLite.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

DEFAULT_DOCKER_URL = (
    "postgresql+psycopg://codestrata:codestrata@127.0.0.1:5432/codestrata"
)


def _find_pg_bin(name: str) -> str | None:
    for candidate in (
        shutil.which(name),
        f"/usr/local/opt/postgresql@16/bin/{name}",
        f"/opt/homebrew/opt/postgresql@16/bin/{name}",
        f"/usr/lib/postgresql/16/bin/{name}",
    ):
        if candidate and Path(candidate).is_file():
            return candidate
    return None


def _port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def try_existing_database_url() -> str | None:
    for key in ("CODESTRATA_DATABASE_URL", "CODESTRATA_PLATFORM_DATABASE_URL"):
        value = os.environ.get(key, "").strip()
        if value and not value.lower().startswith("sqlite"):
            if value.startswith("postgresql://"):
                return "postgresql+psycopg://" + value[len("postgresql://") :]
            if value.startswith("postgres://"):
                return "postgresql+psycopg://" + value[len("postgres://") :]
            return value
    if _port_open("127.0.0.1", 5432):
        return DEFAULT_DOCKER_URL
    return None


@contextmanager
def ephemeral_postgres(data_root: Path) -> Iterator[str]:
    """Start a temporary PostgreSQL instance and yield a SQLAlchemy URL."""

    initdb = _find_pg_bin("initdb")
    pg_ctl = _find_pg_bin("pg_ctl")
    createdb = _find_pg_bin("createdb")
    if not initdb or not pg_ctl or not createdb:
        raise RuntimeError(
            "PostgreSQL client tools (initdb/pg_ctl/createdb) are required for "
            "Platform persistence tests when Docker Compose is unavailable."
        )

    # Keep paths short — macOS unix socket paths are capped (~103 bytes).
    import uuid

    short_root = Path("/tmp") / f"cs-pg-{uuid.uuid4().hex[:10]}"
    data_dir = short_root / "data"
    sock_dir = short_root / "s"
    data_dir.mkdir(parents=True, exist_ok=True)
    sock_dir.mkdir(parents=True, exist_ok=True)
    _ = data_root

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port = int(sock.getsockname()[1])

    subprocess.run(
        [initdb, "-D", str(data_dir), "--auth=trust", "--username=codestrata", "--no-instructions"],
        check=True,
        capture_output=True,
        text=True,
    )
    (data_dir / "postgresql.conf").write_text(
        (data_dir / "postgresql.conf").read_text(encoding="utf-8")
        + (
            "\nlisten_addresses = '127.0.0.1'\n"
            f"port = {port}\n"
            f"unix_socket_directories = '{sock_dir}'\n"
        ),
        encoding="utf-8",
    )
    (data_dir / "pg_hba.conf").write_text(
        "host all all 127.0.0.1/32 trust\nlocal all all trust\n",
        encoding="utf-8",
    )

    log_path = short_root / "postgres.log"
    env = {
        **dict(__import__("os").environ),
        "LC_ALL": "en_US.UTF-8",
        "LANG": "en_US.UTF-8",
    }
    try:
        subprocess.run(
            [pg_ctl, "-D", str(data_dir), "-l", str(log_path), "start"],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        for _ in range(50):
            if _port_open("127.0.0.1", port):
                break
            time.sleep(0.1)
        else:
            raise RuntimeError(f"Ephemeral PostgreSQL failed to become ready; see {log_path}")

        subprocess.run(
            [
                createdb,
                "-h",
                "127.0.0.1",
                "-p",
                str(port),
                "-U",
                "codestrata",
                "codestrata",
            ],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        yield f"postgresql+psycopg://codestrata@127.0.0.1:{port}/codestrata"
    finally:
        subprocess.run(
            [pg_ctl, "-D", str(data_dir), "-m", "immediate", "stop"],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        shutil.rmtree(short_root, ignore_errors=True)


def resolve_test_database_url(data_root: Path | None = None) -> tuple[str, bool]:
    """Return (url, managed). managed=True means caller must stop ephemeral PG."""

    existing = try_existing_database_url()
    if existing is not None:
        # Verify connectivity quickly.
        try:
            import psycopg

            dsn = existing.replace("postgresql+psycopg://", "postgresql://")
            with psycopg.connect(dsn, connect_timeout=2):
                return existing, False
        except Exception:
            pass
    if data_root is None:
        raise RuntimeError("data_root required to start ephemeral PostgreSQL")
    # Caller should use ephemeral_postgres context manager instead.
    raise RuntimeError("No reachable PostgreSQL; use ephemeral_postgres()")
