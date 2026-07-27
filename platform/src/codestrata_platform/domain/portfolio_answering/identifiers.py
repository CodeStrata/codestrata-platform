"""Deterministic portfolio answering identifiers."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.shared.ids import PlatformId

_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,240}$")


def _stable_token(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:32]


@dataclass(frozen=True, slots=True)
class PortfolioAnswerRunId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", PlatformId(self.value).value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class PortfolioAnswerCitationId:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact or not _TOKEN.match(compact):
            raise InvalidValueError(
                "portfolio answer citation id is invalid",
                reason_code="invalid_portfolio_answer_citation_id",
            )
        object.__setattr__(self, "value", compact)


@dataclass(frozen=True, slots=True)
class PortfolioAnswerProjectionKey:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact or len(compact) > 128:
            raise InvalidValueError(
                "portfolio answer projection key is invalid",
                reason_code="invalid_portfolio_answer_projection_key",
            )
        object.__setattr__(self, "value", compact)

    @classmethod
    def from_parts(
        cls,
        *,
        organization_id: str,
        workspace_id: str,
        portfolio_id: str,
        portfolio_retrieval_index_id: str,
        portfolio_retrieval_index_version: int,
        normalized_question_hash: str,
        question_type: str,
        retrieval_policy_version: str,
        prompt_template_version: str,
        answer_policy_version: str,
        provider_id: str,
        model_id: str,
        temperature: float,
        max_output_tokens: int,
    ) -> PortfolioAnswerProjectionKey:
        digest = hashlib.sha256(
            "|".join(
                [
                    organization_id.strip(),
                    workspace_id.strip(),
                    portfolio_id.strip(),
                    portfolio_retrieval_index_id.strip(),
                    str(portfolio_retrieval_index_version),
                    normalized_question_hash.strip(),
                    question_type.strip(),
                    retrieval_policy_version.strip(),
                    prompt_template_version.strip(),
                    answer_policy_version.strip(),
                    provider_id.strip(),
                    model_id.strip(),
                    f"{temperature:.3f}",
                    str(max_output_tokens),
                ]
            ).encode("utf-8")
        ).hexdigest()
        return cls(digest)


def deterministic_portfolio_answer_run_id(
    *,
    portfolio_id: str,
    portfolio_retrieval_index_id: str,
    projection_key: str,
) -> PortfolioAnswerRunId:
    token = _stable_token(portfolio_id, portfolio_retrieval_index_id, projection_key)
    return PortfolioAnswerRunId(f"portfolio-answer:{token}")


def normalize_portfolio_question_hash(question: str) -> str:
    compact = " ".join(question.strip().lower().split())
    return hashlib.sha256(compact.encode("utf-8")).hexdigest()
