"""Report quality and interpretation-policy bundle verification."""

from __future__ import annotations

from verification.engineering_intelligence.contract import EIR_SCHEMA_VERSION
from verification.engineering_intelligence.ingestion import PipelineArtifacts
from verification.engineering_intelligence.models import CheckResult


def check_report_quality(pipeline: PipelineArtifacts) -> list[CheckResult]:
    report = pipeline.report
    checks: list[CheckResult] = [
        CheckResult(
            name="quality:eir_schema_1_0",
            ok=str(report.schema_version) == EIR_SCHEMA_VERSION,
            detail=str(report.schema_version),
            category="report_quality",
        ),
        CheckResult(
            name="quality:interpretation_bundle_id",
            ok=bool(report.interpretation_policy_bundle_id),
            detail=str(report.interpretation_policy_bundle_id)[:48],
            category="report_quality",
        ),
        CheckResult(
            name="quality:confidence_present",
            ok=report.confidence is not None,
            detail=str(getattr(report.confidence, "level", None)),
            category="report_quality",
        ),
        CheckResult(
            name="quality:limitations_present",
            ok=len(report.limitations or ()) > 0,
            detail=f"count={len(report.limitations or ())}",
            category="report_quality",
        ),
    ]
    cats = {
        getattr(getattr(item, "category", None), "value", getattr(item, "category", None))
        for item in (report.limitations or ())
    }
    cat_text = " ".join(str(c).lower() for c in cats if c)
    checks.append(
        CheckResult(
            name="quality:non_temporal_limitation",
            ok="non_temporal" in cat_text or "temporal" in cat_text,
            detail=f"categories={sorted(str(c) for c in cats)}",
            category="report_quality",
            scenario="Q",
        )
    )
    checks.append(
        CheckResult(
            name="quality:selection_bias_or_public_oss_limitation",
            ok="selection_bias" in cat_text or "controlled_fixture" in cat_text,
            detail=f"categories={sorted(str(c) for c in cats)}",
            category="report_quality",
            scenario="Q",
        )
    )
    return checks
