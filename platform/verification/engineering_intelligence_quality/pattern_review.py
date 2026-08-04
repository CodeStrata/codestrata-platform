"""Recurring pattern editorial review."""

from __future__ import annotations

from typing import Any

from verification.engineering_intelligence_quality.contract import KNOWN_ISSUES_REPOS
from verification.engineering_intelligence_quality.models import (
    DefectCandidate,
    EditorialObservation,
)


def review_patterns(
    payload: dict[str, Any],
) -> tuple[dict[str, Any], list[EditorialObservation], list[DefectCandidate]]:
    observations: list[EditorialObservation] = []
    defects: list[DefectCandidate] = []
    patterns = payload.get("recurring_patterns") or []
    if not isinstance(patterns, list):
        patterns = []

    useful = 0
    low_value = 0
    for item in patterns:
        if not isinstance(item, dict):
            continue
        repos = item.get("repository_ids") or item.get("supporting_repository_ids") or []
        if isinstance(repos, list):
            repo_ids = [str(r).removeprefix("repo:") for r in repos]
        else:
            repo_ids = []
        if len(set(repo_ids)) < 2:
            defects.append(
                DefectCandidate(
                    classification="recurring_pattern",
                    statement="pattern supported by fewer than two repositories",
                    section="recurring_patterns",
                    affected_entity_ids=[str(item.get("pattern_id") or item.get("id") or "")],
                    repository_scope=repo_ids,
                    release_impact="blocking",
                    recommended_handling="SV.13_product_fix",
                )
            )
            continue
        denom = item.get("denominator") or item.get("eligible_repository_count")
        statement = str(item.get("statement") or "")
        if denom is None and " of " not in statement.lower():
            observations.append(
                EditorialObservation(
                    observation_id=f"pattern-denom-{item.get('pattern_id') or item.get('id')}",
                    section="recurring_patterns",
                    classification="missing_context",
                    statement="Pattern statement should make denominator explicit",
                    affected_entity_ids=[str(item.get("pattern_id") or "")],
                    recommended_handling="documentation_only",
                )
            )
        if "industry" in statement.lower() and "not" not in statement.lower():
            defects.append(
                DefectCandidate(
                    classification="recurring_pattern",
                    statement="industry-wide claim in pattern wording",
                    section="recurring_patterns",
                    affected_entity_ids=[str(item.get("pattern_id") or "")],
                    release_impact="blocking",
                    recommended_handling="SV.13_product_fix",
                )
            )
        # Known Issues dominance without limitation note
        if repo_ids and set(repo_ids).issubset(KNOWN_ISSUES_REPOS):
            observations.append(
                EditorialObservation(
                    observation_id=f"pattern-demo-only-{item.get('pattern_id') or 'x'}",
                    section="recurring_patterns",
                    classification="missing_context",
                    statement=(
                        "Pattern supported only by intentionally vulnerable/demo repositories; "
                        "do not generalize without limitation"
                    ),
                    repository_scope=repo_ids,
                    recommended_handling="documentation_only",
                    release_impact="material",
                )
            )
            low_value += 1
        else:
            useful += 1

    observations.append(
        EditorialObservation(
            observation_id="pattern-summary",
            section="recurring_patterns",
            classification="useful" if patterns else "unclear",
            statement=f"{len(patterns)} recurring patterns; useful≈{useful} demo-scoped≈{low_value}",
            recommended_handling="no_change",
        )
    )
    review = {
        "ok": not any(d.release_impact == "blocking" for d in defects),
        "pattern_count": len(patterns),
        "summary": "Recurring patterns reviewed for ≥2-repo support and dataset scope",
    }
    return review, observations, defects
