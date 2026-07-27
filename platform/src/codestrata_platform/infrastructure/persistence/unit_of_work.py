"""SQLAlchemy Unit of Work for Platform persistence orchestration."""

from __future__ import annotations

from collections.abc import Callable
from types import TracebackType
from typing import Self

from sqlalchemy.orm import Session

from codestrata_platform.infrastructure.persistence.repositories import (
    SqlAlchemyAssessmentRepository,
    SqlAlchemyOrganizationRepository,
    SqlAlchemyRepositoryRepository,
    SqlAlchemyWorkspaceRepository,
)


class SqlAlchemyUnitOfWork:
    """Transaction boundary wrapping a SQLAlchemy session and repository adapters."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory
        self.session: Session | None = None
        self.organizations: SqlAlchemyOrganizationRepository | None = None
        self.workspaces: SqlAlchemyWorkspaceRepository | None = None
        self.repositories: SqlAlchemyRepositoryRepository | None = None
        self.assessments: SqlAlchemyAssessmentRepository | None = None

    def __enter__(self) -> Self:
        self.begin()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.rollback()
        self.close()

    def begin(self) -> None:
        if self.session is not None:
            raise RuntimeError("Unit of work already started")
        session = self._session_factory()
        self.session = session
        self.organizations = SqlAlchemyOrganizationRepository(session)
        self.workspaces = SqlAlchemyWorkspaceRepository(session)
        self.repositories = SqlAlchemyRepositoryRepository(session)
        self.assessments = SqlAlchemyAssessmentRepository(session)

    def commit(self) -> None:
        if self.session is None:
            raise RuntimeError("Unit of work is not active")
        self.session.commit()

    def rollback(self) -> None:
        if self.session is None:
            return
        self.session.rollback()

    def close(self) -> None:
        if self.session is None:
            return
        self.session.close()
        self.session = None
        self.organizations = None
        self.workspaces = None
        self.repositories = None
        self.assessments = None
