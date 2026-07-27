"""In-memory portfolio answer run repository."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from codestrata_platform.domain.answering.lifecycle import AnswerStatus
from codestrata_platform.domain.portfolio.identifiers import PortfolioId
from codestrata_platform.domain.portfolio_answering.answer import PortfolioAnswerRun
from codestrata_platform.domain.portfolio_answering.identifiers import PortfolioAnswerRunId


class InMemoryPortfolioAnswerRunRepository:
    def __init__(self) -> None:
        self._items: dict[str, PortfolioAnswerRun] = {}
        self._feedback: dict[str, list[dict[str, object]]] = {}

    def get(self, answer_run_id: PortfolioAnswerRunId) -> PortfolioAnswerRun | None:
        item = self._items.get(answer_run_id.value)
        return item.snapshot() if item is not None else None

    def save(self, run: PortfolioAnswerRun) -> None:
        self._items[run.answer_run_id.value] = run.snapshot()

    def find_by_projection_key(self, projection_key: str) -> PortfolioAnswerRun | None:
        key = projection_key.strip()
        matches = [
            item
            for item in self._items.values()
            if item.projection_key.value == key and item.status is AnswerStatus.COMPLETED
        ]
        if not matches:
            return None
        return matches[-1].snapshot()

    def list_by_portfolio(
        self,
        portfolio_id: PortfolioId,
        *,
        limit: int = 50,
    ) -> tuple[PortfolioAnswerRun, ...]:
        items = [
            item.snapshot()
            for item in self._items.values()
            if item.portfolio_id == portfolio_id
        ]
        items.sort(key=lambda item: item.audit.created_at.value, reverse=True)
        return tuple(items[: max(1, limit)])

    def save_feedback(
        self,
        *,
        answer_run_id: PortfolioAnswerRunId,
        rating: int,
        feedback_category: str,
        comment: str,
    ) -> dict[str, object]:
        token = hashlib.sha256(
            f"{answer_run_id.value}|{rating}|{feedback_category}|{comment}|{datetime.now(UTC).isoformat()}".encode()
        ).hexdigest()[:24]
        payload: dict[str, object] = {
            "id": f"portfolio-answer-feedback:{token}",
            "answer_run_id": answer_run_id.value,
            "rating": rating,
            "feedback_category": feedback_category[:64],
            "comment": comment[:1000],
        }
        self._feedback.setdefault(answer_run_id.value, []).append(dict(payload))
        return payload

    def list_feedback(
        self,
        answer_run_id: PortfolioAnswerRunId,
    ) -> tuple[dict[str, object], ...]:
        return tuple(dict(item) for item in self._feedback.get(answer_run_id.value, ()))
