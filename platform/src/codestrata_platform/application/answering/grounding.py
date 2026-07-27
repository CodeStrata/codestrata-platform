"""Grounding validation for generated answers."""

from __future__ import annotations

import re

from codestrata_platform.application.answering.citations import citations_from_context
from codestrata_platform.application.answering.policies import confidence_from_grounding
from codestrata_platform.application.retrieval.context import RetrievalContext
from codestrata_platform.domain.answering.citation import AnswerCitation, AnswerConfidence
from codestrata_platform.domain.answering.grounding import (
    AnswerText,
    GroundingIssue,
    GroundingResult,
)
from codestrata_platform.domain.answering.lifecycle import (
    ContextSufficiencyStatus,
    GroundingStatus,
)

_CITATION_RE = re.compile(r"\[C\d+\]")
_UNSUPPORTED_MARKERS = (
    "i inspected the repository source",
    "raw source code shows",
    "i accessed the filesystem",
    "guaranteed to fix",
)


class DefaultGroundingPolicy:
    allow_partial = True


class AnswerGroundingValidator:
    def __init__(self, policy: DefaultGroundingPolicy | None = None) -> None:
        self._policy = policy or DefaultGroundingPolicy()

    def validate(
        self,
        *,
        generated_text: str,
        context: RetrievalContext,
        sufficiency: ContextSufficiencyStatus,
    ) -> tuple[AnswerText, tuple[AnswerCitation, ...], GroundingResult, AnswerConfidence]:
        citations = citations_from_context(context)
        allowed = {item.label for item in citations}
        used = tuple(sorted(set(_CITATION_RE.findall(generated_text))))
        issues: list[GroundingIssue] = []
        unknown = [label for label in used if label not in allowed]
        for label in unknown:
            issues.append(
                GroundingIssue(
                    code="unknown_citation",
                    message=f"Citation {label} is not present in supplied context",
                    severity="error",
                )
            )
        lowered = generated_text.lower()
        for marker in _UNSUPPORTED_MARKERS:
            if marker in lowered:
                issues.append(
                    GroundingIssue(
                        code="unsupported_claim",
                        message=f"Unsupported claim marker detected: {marker}",
                        severity="error",
                    )
                )
        if sufficiency is ContextSufficiencyStatus.INSUFFICIENT:
            status = GroundingStatus.INSUFFICIENT_CONTEXT
        elif unknown or any(item.code == "unsupported_claim" for item in issues):
            status = GroundingStatus.UNGROUNDED
        elif not used and citations:
            status = GroundingStatus.PARTIALLY_GROUNDED
            issues.append(
                GroundingIssue(
                    code="missing_citations",
                    message="Answer did not cite retrieved context labels",
                    severity="warning",
                )
            )
        elif used and len(used) < max(1, len(citations) // 3):
            status = GroundingStatus.PARTIALLY_GROUNDED
        else:
            status = GroundingStatus.GROUNDED

        if status is GroundingStatus.UNGROUNDED and not self._policy.allow_partial:
            status = GroundingStatus.UNGROUNDED

        level, score, factors = confidence_from_grounding(
            sufficiency=sufficiency,
            grounding=status,
            citation_count=len(used),
            chunk_count=len(context.items),
        )
        used_citations = tuple(item for item in citations if item.label in used) or citations
        return (
            AnswerText(generated_text),
            used_citations,
            GroundingResult(status=status, issues=tuple(issues), cited_labels=used),
            AnswerConfidence(
                level=level,
                score=score,
                factors=factors,
                policy_version="1.0.0",
            ),
        )


CitationValidator = AnswerGroundingValidator
UnsupportedClaimDetector = AnswerGroundingValidator
GroundingPolicy = DefaultGroundingPolicy
