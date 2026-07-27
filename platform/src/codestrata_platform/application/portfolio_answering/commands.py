"""Portfolio answering application commands and queries."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.portfolio.identifiers import PortfolioId
from codestrata_platform.domain.portfolio_answering.identifiers import PortfolioAnswerRunId
from codestrata_platform.domain.portfolio_answering.lifecycle import PortfolioQuestionType
from codestrata_platform.domain.portfolio_answering.question import PortfolioQuestionScope
from codestrata_platform.domain.portfolio_retrieval.identifiers import PortfolioRetrievalIndexId


@dataclass(frozen=True, slots=True)
class AskPortfolioQuestionCommand:
    question: str
    scope: PortfolioQuestionScope
    question_type: PortfolioQuestionType | None = None
    portfolio_retrieval_index_id: PortfolioRetrievalIndexId | None = None
    include_diagnostics: bool = False
    use_cache: bool = True


@dataclass(frozen=True, slots=True)
class SubmitPortfolioAnswerFeedbackCommand:
    answer_run_id: PortfolioAnswerRunId
    rating: int
    feedback_category: str
    comment: str = ""


@dataclass(frozen=True, slots=True)
class GetPortfolioAnswerRunQuery:
    answer_run_id: PortfolioAnswerRunId


@dataclass(frozen=True, slots=True)
class ListPortfolioAnswersQuery:
    portfolio_id: PortfolioId
    limit: int = 50
