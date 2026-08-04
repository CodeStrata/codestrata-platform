"""Determinism checks for the repaired 22-repository EI build."""

from __future__ import annotations

from typing import Any

from verification.engineering_intelligence.ingestion import build_pipeline_from_assessments
from verification.engineering_intelligence_quality.inputs import (
    load_prepared_assessments_from_sv10,
)
from verification.system_defect_fixes.models import CheckResult


def check_order_independent_ids(monorepo: Any = None) -> list[CheckResult]:
    assessments, _sv11, _meta = load_prepared_assessments_from_sv10(monorepo=monorepo)
    forward = build_pipeline_from_assessments(
        assessments,
        title="SV.13 determinism forward",
    )
    reverse = build_pipeline_from_assessments(
        list(reversed(assessments)),
        title="SV.13 determinism reverse",
    )
    fwd_ids = {
        "dataset": forward.ingest_result.dataset.dataset_id,
        "aggregation": forward.aggregation.aggregation_id,
        "report": forward.report.report_id,
    }
    rev_ids = {
        "dataset": reverse.ingest_result.dataset.dataset_id,
        "aggregation": reverse.aggregation.aggregation_id,
        "report": reverse.report.report_id,
    }
    return [
        CheckResult(
            name="order_independent_dataset_id",
            ok=fwd_ids["dataset"] == rev_ids["dataset"],
            detail=f"forward={fwd_ids['dataset']} reverse={rev_ids['dataset']}",
        ),
        CheckResult(
            name="order_independent_aggregation_id",
            ok=fwd_ids["aggregation"] == rev_ids["aggregation"],
            detail=f"forward={fwd_ids['aggregation']} reverse={rev_ids['aggregation']}",
        ),
        CheckResult(
            name="order_independent_report_id",
            ok=fwd_ids["report"] == rev_ids["report"],
            detail=f"forward={fwd_ids['report']} reverse={rev_ids['report']}",
        ),
    ]
