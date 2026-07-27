"""Grounding validation for generated portfolio answers."""

from __future__ import annotations

import re

from codestrata_platform.application.portfolio_answering.citations import citations_from_context
from codestrata_platform.application.portfolio_answering.policies import confidence_from_grounding
from codestrata_platform.application.portfolio_retrieval.models import PortfolioRetrievalContext
from codestrata_platform.domain.answering.grounding import (
    AnswerText,
    GroundingIssue,
    GroundingResult,
)
from codestrata_platform.domain.answering.lifecycle import (
    ContextSufficiencyStatus,
    GroundingStatus,
)
from codestrata_platform.domain.portfolio_answering.citation import (
    PortfolioAnswerCitation,
    PortfolioAnswerConfidence,
)

_CITATION_RE = re.compile(r"\[P\d+\]")
_FOREIGN_CITATION_RE = re.compile(r"\[C\d+\]")
_UNSUPPORTED_MARKERS = (
    "i inspected the repository source",
    "raw source code shows",
    "i accessed the filesystem",
    "guaranteed to fix",
    "from the repository graph",
    "from ceim",
    "from the engineering snapshot directly",
)


class DefaultPortfolioGroundingPolicy:
    allow_partial = True


class PortfolioAnswerGroundingValidator:
    def __init__(self, policy: DefaultPortfolioGroundingPolicy | None = None) -> None:
        self._policy = policy or DefaultPortfolioGroundingPolicy()

    def validate(
        self,
        *,
        generated_text: str,
        context: PortfolioRetrievalContext,
        sufficiency: ContextSufficiencyStatus,
        portfolio_id: str,
        portfolio_snapshot_id: str,
    ) -> tuple[
        AnswerText,
        tuple[PortfolioAnswerCitation, ...],
        GroundingResult,
        PortfolioAnswerConfidence,
    ]:
        citations = citations_from_context(
            context,
            portfolio_id=portfolio_id,
            portfolio_snapshot_id=portfolio_snapshot_id,
        )
        allowed = {item.label for item in citations}
        used = tuple(sorted(set(_CITATION_RE.findall(generated_text))))
        issues: list[GroundingIssue] = []
        unknown = [label for label in used if label not in allowed]
        for label in unknown:
            issues.append(
                GroundingIssue(
                    code="unknown_citation",
                    message=f"Citation {label} is not present in supplied portfolio context",
                    severity="error",
                )
            )
        foreign = tuple(sorted(set(_FOREIGN_CITATION_RE.findall(generated_text))))
        for label in foreign:
            issues.append(
                GroundingIssue(
                    code="foreign_citation_namespace",
                    message=f"Citation {label} is not a portfolio context label",
                    severity="error",
                )
            )
        for citation in citations:
            if (
                citation.portfolio_id != portfolio_id
                or citation.portfolio_snapshot_id != portfolio_snapshot_id
            ):
                issues.append(
                    GroundingIssue(
                        code="cross_portfolio_citation",
                        message=(
                            f"Citation {citation.label} provenance does not match the "
                            "answer portfolio snapshot"
                        ),
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
        provenance_error = any(item.code == "cross_portfolio_citation" for item in issues)
        foreign_error = any(item.code == "foreign_citation_namespace" for item in issues)
        if sufficiency is ContextSufficiencyStatus.INSUFFICIENT:
            status = GroundingStatus.INSUFFICIENT_CONTEXT
        elif (
            unknown
            or foreign_error
            or provenance_error
            or any(item.code == "unsupported_claim" for item in issues)
        ):
            status = GroundingStatus.UNGROUNDED
        elif not used and citations:
            status = GroundingStatus.PARTIALLY_GROUNDED
            issues.append(
                GroundingIssue(
                    code="missing_citations",
                    message="Answer did not cite retrieved portfolio context labels",
                    severity="warning",
                )
            )
        elif used and len(used) < max(1, len(citations) // 3):
            status = GroundingStatus.PARTIALLY_GROUNDED
        else:
            status = GroundingStatus.GROUNDED

        if status is GroundingStatus.UNGROUNDED and not self._policy.allow_partial:
            status = GroundingStatus.UNGROUNDED

        diagnostic_kinds = tuple(sorted({item.kind for item in context.diagnostics}))
        level, score, factors = confidence_from_grounding(
            sufficiency=sufficiency,
            grounding=status,
            citation_count=len(used),
            chunk_count=len(context.items),
            repository_count=context.repository_count,
            diagnostic_kinds=diagnostic_kinds,
        )
        used_citations = tuple(item for item in citations if item.label in used) or citations
        return (
            AnswerText(generated_text),
            used_citations,
            GroundingResult(status=status, issues=tuple(issues), cited_labels=used),
            PortfolioAnswerConfidence(
                level=level,
                score=score,
                factors=factors,
                policy_version="1.0.0",
            ),
        )
