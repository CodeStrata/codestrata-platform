"""Portfolio answer run persistence ports."""

from __future__ import annotations

from typing import Protocol

from codestrata_platform.domain.portfolio.identifiers import PortfolioId
from codestrata_platform.domain.portfolio_answering.answer import PortfolioAnswerRun
from codestrata_platform.domain.portfolio_answering.identifiers import PortfolioAnswerRunId


class PortfolioAnswerRunRepository(Protocol):
    def get(self, answer_run_id: PortfolioAnswerRunId) -> PortfolioAnswerRun | None: ...

    def save(self, run: PortfolioAnswerRun) -> None: ...

    def find_by_projection_key(self, projection_key: str) -> PortfolioAnswerRun | None: ...

    def list_by_portfolio(
        self,
        portfolio_id: PortfolioId,
        *,
        limit: int = 50,
    ) -> tuple[PortfolioAnswerRun, ...]: ...

    def save_feedback(
        self,
        *,
        answer_run_id: PortfolioAnswerRunId,
        rating: int,
        feedback_category: str,
        comment: str,
    ) -> dict[str, object]: ...

    def list_feedback(
        self,
        answer_run_id: PortfolioAnswerRunId,
    ) -> tuple[dict[str, object], ...]: ...
