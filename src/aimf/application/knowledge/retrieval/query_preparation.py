"""Deterministic retrieval query preparation (Phase 5.5).

No query rewriting, synonym expansion, or LLM execution.
"""

from __future__ import annotations

import re

from aimf.domain.knowledge.identifiers import fingerprint_payload
from aimf.domain.knowledge.retrieval import RetrievalDiagnostic, RetrievalQuery

_WHITESPACE = re.compile(r"\s+")


class QueryPreparationError(ValueError):
    """Raised when a retrieval query cannot be prepared."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def as_diagnostic(self) -> RetrievalDiagnostic:
        return RetrievalDiagnostic(
            code=self.code,
            message=self.message,
            severity="error",
        )


def prepare_retrieval_query(
    raw: str,
    *,
    max_query_characters: int,
) -> RetrievalQuery:
    """Trim/normalize whitespace, reject empty/oversized queries, fingerprint."""

    original = str(raw)
    if len(original) > max_query_characters:
        raise QueryPreparationError(
            "query_too_large",
            f"query exceeds max_query_characters ({max_query_characters})",
        )
    normalized = _WHITESPACE.sub(" ", original).strip()
    if not normalized:
        raise QueryPreparationError("empty_query", "query must not be empty")
    fingerprint = fingerprint_payload(
        {
            "normalized": normalized,
            "max_query_characters": max_query_characters,
        }
    )
    return RetrievalQuery(
        original=original,
        normalized=normalized,
        fingerprint=fingerprint,
    )
