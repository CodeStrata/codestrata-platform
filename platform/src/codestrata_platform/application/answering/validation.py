"""Deterministic question classification."""

from __future__ import annotations

from codestrata_platform.domain.answering.lifecycle import QuestionType


class DeterministicQuestionClassificationPolicy:
    """Rule-based question classification (no LLM)."""

    def classify(self, question_text: str) -> QuestionType:
        text = question_text.lower()
        if any(token in text for token in ("impact", "affected", "change affect")):
            if "technolog" in text:
                return QuestionType.TECHNOLOGY_IMPACT
            return QuestionType.COMPONENT_IMPACT
        if any(token in text for token in ("finding", "severity", "evidence", "highest-risk")):
            return QuestionType.FINDING_EXPLANATION
        if any(token in text for token in ("recommendation", "priority", "next step")):
            return QuestionType.RECOMMENDATION_EXPLANATION
        if any(token in text for token in ("risk", "hotspot")):
            return QuestionType.RISK_EXPLANATION
        if any(token in text for token in ("dependency", "cycle", "upstream", "downstream")):
            return QuestionType.DEPENDENCY_EXPLANATION
        if any(token in text for token in ("trace", "traceability", "linked to")):
            return QuestionType.TRACEABILITY_EXPLANATION
        if any(token in text for token in ("modernization", "modernize", "roadmap")):
            return QuestionType.MODERNIZATION_GUIDANCE
        if any(token in text for token in ("overview", "summary", "inventory")):
            return QuestionType.REPOSITORY_OVERVIEW
        if "technolog" in text:
            return QuestionType.TECHNOLOGY_EXPLANATION
        return QuestionType.GENERAL_ENGINEERING_QUESTION


class QuestionClassificationService:
    def __init__(
        self,
        policy: DeterministicQuestionClassificationPolicy | None = None,
    ) -> None:
        self._policy = policy or DeterministicQuestionClassificationPolicy()

    def classify(
        self,
        question_text: str,
        *,
        override: QuestionType | None = None,
    ) -> QuestionType:
        if override is not None:
            return override
        return self._policy.classify(question_text)
