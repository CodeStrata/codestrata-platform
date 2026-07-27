"""Domain package for Engineering Answering."""

from __future__ import annotations

from codestrata_platform.domain.answering.answer import EngineeringAnswerRun
from codestrata_platform.domain.answering.citation import AnswerCitation, AnswerConfidence
from codestrata_platform.domain.answering.grounding import AnswerText, GroundingResult
from codestrata_platform.domain.answering.identifiers import AnswerRunId
from codestrata_platform.domain.answering.lifecycle import (
    AnswerConfidenceLevel,
    AnswerStatus,
    GroundingStatus,
    QuestionType,
)
from codestrata_platform.domain.answering.ports import LLMProvider
from codestrata_platform.domain.answering.question import EngineeringQuestion, QuestionScope

__all__ = [
    "AnswerCitation",
    "AnswerConfidence",
    "AnswerConfidenceLevel",
    "AnswerRunId",
    "AnswerStatus",
    "AnswerText",
    "EngineeringAnswerRun",
    "EngineeringQuestion",
    "GroundingResult",
    "GroundingStatus",
    "LLMProvider",
    "QuestionScope",
    "QuestionType",
]
