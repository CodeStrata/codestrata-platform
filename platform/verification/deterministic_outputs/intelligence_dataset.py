"""IntelligenceDataset / aggregation / EIR order-independence."""

from __future__ import annotations

from typing import Any

from verification.deterministic_outputs.models import CheckResult, DeterminismDefect
from verification.deterministic_outputs.ordering import (
    group_by_language,
    group_by_tier_proxy,
    reversed_list,
    shuffled_deterministic,
)
from verification.engineering_intelligence.ingestion import build_pipeline_from_assessments
from verification.engineering_intelligence_quality.inputs import (
    load_prepared_assessments_from_sv10,
)


def _ids(pipeline: Any) -> dict[str, str]:
    dataset_id = pipeline.ingest_result.dataset.dataset_id
    if hasattr(dataset_id, "value"):
        dataset_id = dataset_id.value
    report_id = pipeline.report.report_id
    if hasattr(report_id, "value"):
        report_id = report_id.value
    return {
        "dataset": str(dataset_id),
        "aggregation": str(pipeline.aggregation.aggregation_id),
        "report": str(report_id),
        "bundle": str(getattr(pipeline.report, "interpretation_policy_bundle_id", "") or ""),
        "included": str(len(pipeline.ingest_result.included)),
        "drilldowns": str(len(getattr(pipeline.report, "repository_drilldowns", ()) or ())),
        "patterns": str(len(getattr(pipeline.report, "recurring_patterns", ()) or ())),
        "observations": str(
            len(getattr(pipeline.report, "modernization_observations", ()) or ())
        ),
    }


def check_intelligence_pipeline_order(monorepo) -> tuple[list[CheckResult], list[DeterminismDefect]]:
    assessments, _sv11, _meta = load_prepared_assessments_from_sv10(monorepo=monorepo)
    variants = {
        "catalog": list(assessments),
        "reverse": reversed_list(assessments),
        "language": group_by_language(assessments),
        "tier_proxy": group_by_tier_proxy(assessments),
        "shuffled": shuffled_deterministic(assessments, seed=15),
    }
    results: dict[str, dict[str, str]] = {}
    for name, items in variants.items():
        pipeline = build_pipeline_from_assessments(
            items,
            title=f"SV.15 determinism {name}",
        )
        results[name] = _ids(pipeline)

    baseline = results["catalog"]
    checks: list[CheckResult] = []
    defects: list[DeterminismDefect] = []
    for name, ids in results.items():
        ok = ids == baseline
        checks.append(
            CheckResult(
                name=f"ei_order_invariant_{name}",
                ok=ok,
                detail=f"dataset={ids['dataset']} report={ids['report']}",
                category="intelligence",
            )
        )
        if not ok:
            defects.append(
                DeterminismDefect(
                    classification="merge_order",
                    contract="EngineeringIntelligenceReport",
                    expected=str(baseline),
                    actual=str(ids),
                    detail=f"variant={name}",
                    affected_ids=[ids["dataset"], ids["report"]],
                )
            )

    # Technology / capability presence (non-empty for 22-repo dataset).
    pipeline = build_pipeline_from_assessments(
        assessments,
        title="SV.15 technology check",
    )
    tech = getattr(pipeline.report, "technology_distribution", None)
    caps = getattr(pipeline.report, "capability_comparisons", None)
    checks.append(
        CheckResult(
            name="ei_technology_distribution_present",
            ok=tech is not None,
            detail="technology_distribution section",
            category="intelligence",
        )
    )
    checks.append(
        CheckResult(
            name="ei_capability_comparisons_present",
            ok=caps is not None,
            detail="capability_comparisons section",
            category="intelligence",
        )
    )
    checks.append(
        CheckResult(
            name="ei_population_22",
            ok=baseline["included"] == "22" and baseline["drilldowns"] == "22",
            detail=f"included={baseline['included']} drilldowns={baseline['drilldowns']}",
            category="intelligence",
        )
    )
    return checks, defects


# Module aliases expected by package layout.
def check_intelligence_dataset(monorepo):
    checks, defects = check_intelligence_pipeline_order(monorepo)
    return [c for c in checks if "order" in c.name or "population" in c.name], defects


def check_aggregation(monorepo):
    checks, defects = check_intelligence_pipeline_order(monorepo)
    return [c for c in checks if "order" in c.name], defects


def check_engineering_intelligence(monorepo):
    return check_intelligence_pipeline_order(monorepo)
