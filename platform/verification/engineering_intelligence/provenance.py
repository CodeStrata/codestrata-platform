"""Provenance checks for populated intelligence sections."""

from __future__ import annotations

from verification.engineering_intelligence.ingestion import PipelineArtifacts
from verification.engineering_intelligence.models import CheckResult


def check_provenance(pipeline: PipelineArtifacts) -> list[CheckResult]:
    report = pipeline.report
    included = set(pipeline.ingest_result.dataset.included_repository_ids)
    checks: list[CheckResult] = []

    # Capability snapshots / comparisons should reference included repositories.
    orphan_caps = []
    for comp in report.capability_comparisons or ():
        snaps = getattr(comp, "snapshots", ()) or getattr(comp, "repository_snapshots", ())
        for snap in snaps:
            rid = getattr(snap, "repository_id", None)
            if rid and rid not in included:
                orphan_caps.append(rid)
    checks.append(
        CheckResult(
            name="provenance:capability_repos_included",
            ok=not orphan_caps,
            detail=f"orphans={len(set(orphan_caps))}",
            category="provenance",
        )
    )

    orphan_patterns = []
    for pattern in report.recurring_patterns or ():
        repos = getattr(pattern, "repository_ids", None) or getattr(
            pattern, "supporting_repository_ids", ()
        )
        for rid in repos or ():
            if rid not in included:
                orphan_patterns.append(rid)
    checks.append(
        CheckResult(
            name="provenance:pattern_repos_included",
            ok=not orphan_patterns,
            detail=f"orphans={len(set(orphan_patterns))}",
            category="provenance",
        )
    )

    orphan_mods = []
    for obs in report.modernization_observations or ():
        repos = getattr(obs, "supporting_repository_ids", None) or getattr(
            obs, "repository_ids", ()
        )
        for rid in repos or ():
            if rid not in included:
                orphan_mods.append(rid)
    checks.append(
        CheckResult(
            name="provenance:modernization_repos_included",
            ok=not orphan_mods,
            detail=f"orphans={len(set(orphan_mods))}",
            category="provenance",
        )
    )

    # Dataset linked on report
    checks.append(
        CheckResult(
            name="provenance:report_dataset_link",
            ok=report.dataset.dataset_id.value
            == pipeline.ingest_result.dataset.dataset_id.value,
            detail=report.dataset.dataset_id.value,
            category="provenance",
        )
    )
    return checks
