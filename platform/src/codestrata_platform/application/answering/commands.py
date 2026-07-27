"""Answering application commands and queries."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.answering.identifiers import AnswerRunId
from codestrata_platform.domain.answering.lifecycle import QuestionType
from codestrata_platform.domain.answering.question import QuestionScope
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.retrieval.identifiers import RetrievalIndexId


@dataclass(frozen=True, slots=True)
class AskEngineeringQuestionCommand:
    question: str
    scope: QuestionScope
    question_type: QuestionType | None = None
    retrieval_index_id: RetrievalIndexId | None = None
    include_diagnostics: bool = False
    use_cache: bool = True


@dataclass(frozen=True, slots=True)
class SubmitAnswerFeedbackCommand:
    answer_run_id: AnswerRunId
    rating: int
    feedback_category: str
    comment: str = ""


@dataclass(frozen=True, slots=True)
class GetAnswerRunQuery:
    answer_run_id: AnswerRunId


@dataclass(frozen=True, slots=True)
class ListRepositoryAnswersQuery:
    repository_id: RepositoryId
    limit: int = 50
