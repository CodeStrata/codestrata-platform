"""Threshold filtering for modernization observation candidates."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from codestrata_platform.intelligence_reporting.application.modernization_observations.candidates import (
    ModernizationObservationCandidate,
)
from codestrata_platform.intelligence_reporting.application.modernization_observations.policy import (
    ModernizationObservationPolicy,
)


def filter_threshold_candidates(
    candidates: Sequence[ModernizationObservationCandidate],
    *,
    policy: ModernizationObservationPolicy,
    denominator_for_candidate: Callable[[ModernizationObservationCandidate], set[str]],
) -> tuple[
    list[ModernizationObservationCandidate],
    list[ModernizationObservationCandidate],
    int,
]:
    accepted: list[ModernizationObservationCandidate] = []
    rejected: list[ModernizationObservationCandidate] = []
    unavailable_denom = 0
    for candidate in candidates:
        denom_ids = denominator_for_candidate(candidate)
        denom = len(denom_ids)
        if denom == 0:
            unavailable_denom += 1
            candidate.rejection_reason = "denominator_unavailable"
            rejected.append(candidate)
            continue
        # Distinct recommendation-backed repositories within denominator.
        present = sorted(
            {
                ref.repository_id
                for ref in candidate.recommendation_refs
                if ref.repository_id in denom_ids
            }
        )
        if len(present) < policy.minimum_repository_count:
            candidate.rejection_reason = "below_minimum_repository_count"
            rejected.append(candidate)
            continue
        ratio = len(present) / denom
        if ratio < policy.minimum_repository_ratio:
            candidate.rejection_reason = "below_minimum_repository_ratio"
            rejected.append(candidate)
            continue
        # Restrict recommendation refs to denominator-eligible repos for emission.
        candidate.recommendation_refs = [
            ref for ref in candidate.recommendation_refs if ref.repository_id in set(present)
        ]
        candidate.priority_action_refs = [
            ref
            for ref in candidate.priority_action_refs
            if ref.repository_id in set(present)
        ]
        candidate.roadmap_refs = [
            ref for ref in candidate.roadmap_refs if ref.repository_id in set(present)
        ]
        accepted.append(candidate)
    return accepted, rejected, unavailable_denom
