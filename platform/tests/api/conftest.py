"""Shared fixtures for Platform REST API tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from codestrata_platform.api import create_app
from codestrata_platform.infrastructure.persistence import (
    create_engine_from_url,
    create_platform_schema,
)

_PERSISTENCE_TESTS = Path(__file__).resolve().parents[1] / "persistence"
if str(_PERSISTENCE_TESTS) not in sys.path:
    sys.path.insert(0, str(_PERSISTENCE_TESTS))

from postgres_support import ephemeral_postgres, try_existing_database_url  # noqa: E402


@pytest.fixture(scope="session")
def api_postgres_url(tmp_path_factory):
    existing = try_existing_database_url()
    if existing is not None:
        try:
            engine = create_engine_from_url(existing)
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            engine.dispose()
            yield existing
            return
        except Exception:
            pass
    data_root = tmp_path_factory.mktemp("api-pg")
    with ephemeral_postgres(Path(data_root)) as url:
        yield url


@pytest.fixture
def client() -> TestClient:
    app = create_app(use_memory=True)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def durable_client(api_postgres_url: str, tmp_path) -> TestClient:
    engine = create_engine_from_url(api_postgres_url)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    create_platform_schema(engine)
    engine.dispose()
    artifact_root = tmp_path / "artifacts"
    app = create_app(
        database_url=api_postgres_url,
        artifact_storage_root=artifact_root,
    )
    with TestClient(app) as test_client:
        yield test_client
