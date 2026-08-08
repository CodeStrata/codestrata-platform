"""Query planning errors (bounded codes; no raw AWS/boto strings)."""

from __future__ import annotations


class InsightsQueryPlanError(ValueError):
    """Deterministic query-plan failure with a stable error code."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(code if not detail else f"{code}:{detail}")
