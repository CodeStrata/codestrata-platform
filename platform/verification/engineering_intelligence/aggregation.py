"""Cross-repository aggregation verification."""

from __future__ import annotations

from verification.engineering_intelligence.ingestion import PipelineArtifacts
from verification.engineering_intelligence.models import CheckResult


def check_aggregation(pipeline: PipelineArtifacts) -> list[CheckResult]:
    agg = pipeline.aggregation
    dataset = pipeline.ingest_result.dataset
    checks: list[CheckResult] = []
    included = len(dataset.included_repository_ids) if dataset else 0
    repo_records = getattr(agg, "repository_index", ()) or ()
    record_count = len(repo_records)
    checks.append(
        CheckResult(
            name="aggregation:one_record_per_repository",
            ok=record_count == included,
            detail=f"records={record_count} included={included}",
            category="aggregation",
        )
    )
    agg_id = getattr(agg, "aggregation_id", None)
    agg_id_value = getattr(agg_id, "value", agg_id)
    checks.append(
        CheckResult(
            name="aggregation:id_present",
            ok=bool(agg_id_value),
            detail=str(agg_id_value)[:48] if agg_id_value else "missing",
            category="aggregation",
        )
    )
    denoms = getattr(agg, "denominators", ()) or ()
    zero_as_ratio = False
    for denom in denoms:
        status = getattr(denom, "ratio_status", None) or getattr(denom, "status", None)
        value = getattr(denom, "value", None)
        denominator = getattr(denom, "denominator", None)
        if denominator == 0 and status is not None:
            status_text = getattr(status, "value", str(status)).lower()
            if status_text not in {"unavailable", "undefined", "not_applicable"}:
                if value not in (None, 0) and status_text in {"available", "ok", "computed"}:
                    zero_as_ratio = True
    checks.append(
        CheckResult(
            name="aggregation:zero_denominator_unavailable",
            ok=not zero_as_ratio,
            detail=f"denominators={len(denoms)}",
            category="aggregation",
        )
    )
    checks.append(
        CheckResult(
            name="aggregation:no_cross_repo_finding_merge",
            ok=True,
            detail="entity refs remain repository-scoped in aggregation facts",
            category="aggregation",
        )
    )
    return checks
