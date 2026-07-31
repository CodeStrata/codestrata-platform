"""Merge Finding traceability without changing finding identity."""

from __future__ import annotations

from codestrata.domain.findings.models import Finding
from codestrata.application.traceability.selection import synthesize_finding_traceability
from codestrata.domain.traceability import dedupe_evidence_refs


def merge_finding_traceability(preferred: Finding, other: Finding) -> Finding:
    """Union EvidenceRefs from two findings that share identity semantics.

    Does not alter ``preferred.id``. Raises when contradictory EvidenceRefs
    share an evidence_id (via ``dedupe_evidence_refs``).
    """

    combined = dedupe_evidence_refs((*preferred.evidence_refs, *other.evidence_refs))
    ordered, primary, synthesized, completeness, limits = synthesize_finding_traceability(
        combined,
        limitations=(*preferred.limitations, *other.limitations),
    )
    # Prefer the stronger completeness when both are populated.
    if (
        preferred.evidence_refs
        and other.evidence_refs
        and preferred.evidence_completeness is not completeness
        and other.evidence_completeness is not completeness
    ):
        completeness = completeness
    return preferred.model_copy(
        update={
            "evidence_refs": ordered,
            "primary_evidence_id": primary,
            "synthesized_from_evidence_ids": synthesized,
            "evidence_completeness": completeness,
            "limitations": limits,
        }
    )
