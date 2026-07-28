"""Fixtures for Platform durable persistence tests (PostgreSQL only)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from codestrata_platform.infrastructure.persistence import (
    SqlAlchemyAssessmentArtifactRepository,
    SqlAlchemyAssessmentIntelligenceRepository,
    SqlAlchemyAssessmentRepository,
    SqlAlchemyFindingRepository,
    SqlAlchemyMetricRepository,
    SqlAlchemyOrganizationRepository,
    SqlAlchemyRecommendationRepository,
    SqlAlchemyRepositoryRepository,
    SqlAlchemyUnitOfWork,
    SqlAlchemyWorkspaceRepository,
    create_engine_from_url,
    create_platform_schema,
    create_session_factory,
)

from .postgres_support import ephemeral_postgres, try_existing_database_url


@pytest.fixture(scope="session")
def postgres_url(tmp_path_factory) -> Iterator[str]:
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
    data_root = tmp_path_factory.mktemp("platform-pg")
    with ephemeral_postgres(Path(data_root)) as url:
        yield url


@pytest.fixture
def postgres_engine(postgres_url: str) -> Iterator[Engine]:
    engine = create_engine_from_url(postgres_url)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    create_platform_schema(engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def session_factory(postgres_engine: Engine):
    return create_session_factory(postgres_engine)


@pytest.fixture
def session(session_factory) -> Iterator[Session]:
    db = session_factory()
    try:
        yield db
        db.commit()
    finally:
        db.close()


@pytest.fixture
def org_repo(session: Session) -> SqlAlchemyOrganizationRepository:
    return SqlAlchemyOrganizationRepository(session)


@pytest.fixture
def workspace_repo(session: Session) -> SqlAlchemyWorkspaceRepository:
    return SqlAlchemyWorkspaceRepository(session)


@pytest.fixture
def repository_repo(session: Session) -> SqlAlchemyRepositoryRepository:
    return SqlAlchemyRepositoryRepository(session)


@pytest.fixture
def assessment_repo(session: Session) -> SqlAlchemyAssessmentRepository:
    return SqlAlchemyAssessmentRepository(session)


@pytest.fixture
def artifact_repo(session: Session) -> SqlAlchemyAssessmentArtifactRepository:
    return SqlAlchemyAssessmentArtifactRepository(session)


@pytest.fixture
def intelligence_repo(session: Session) -> SqlAlchemyAssessmentIntelligenceRepository:
    return SqlAlchemyAssessmentIntelligenceRepository(session)


@pytest.fixture
def finding_repo(session: Session) -> SqlAlchemyFindingRepository:
    return SqlAlchemyFindingRepository(session)


@pytest.fixture
def metric_repo(session: Session) -> SqlAlchemyMetricRepository:
    return SqlAlchemyMetricRepository(session)


@pytest.fixture
def recommendation_repo(session: Session) -> SqlAlchemyRecommendationRepository:
    return SqlAlchemyRecommendationRepository(session)


@pytest.fixture
def uow(session_factory) -> Iterator[SqlAlchemyUnitOfWork]:
    unit = SqlAlchemyUnitOfWork(session_factory)
    unit.begin()
    try:
        yield unit
    finally:
        unit.close()
