"""EIR determinism and report-quality identity stability."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.domain.serialization import (
    from_stable_dict,
    report_to_stable_dict,
)

from verification.deterministic_outputs.intelligence_dataset import (
    check_intelligence_pipeline_order,
)
from verification.deterministic_outputs.models import CheckResult
from verification.engineering_intelligence.ingestion import build_pipeline_from_assessments
from verification.engineering_intelligence_quality.inputs import (
    load_prepared_assessments_from_sv10,
)


def check_engineering_intelligence(monorepo):
    checks, defects = check_intelligence_pipeline_order(monorepo)
    assessments, _sv11, _meta = load_prepared_assessments_from_sv10(monorepo=monorepo)
    pipeline = build_pipeline_from_assessments(
        assessments,
        title="SV.15 EIR roundtrip",
    )
    payload = report_to_stable_dict(pipeline.report)
    restored = from_stable_dict(payload)
    again = report_to_stable_dict(restored)
    rid1 = payload.get("report_id")
    rid2 = again.get("report_id")
    bundle1 = payload.get("interpretation_policy_bundle_id")
    bundle2 = again.get("interpretation_policy_bundle_id")
    checks.append(
        CheckResult(
            name="eir_roundtrip_report_id",
            ok=rid1 == rid2,
            detail=f"report_id={rid1}",
            category="eir",
        )
    )
    checks.append(
        CheckResult(
            name="eir_roundtrip_interpretation_bundle",
            ok=bundle1 == bundle2 and bool(bundle1),
            detail=f"bundle={bundle1}",
            category="eir",
        )
    )
    checks.append(
        CheckResult(
            name="eir_schema_version_1_0",
            ok=again.get("schema_version") == "1.0",
            detail=f"schema_version={again.get('schema_version')}",
            category="eir",
        )
    )
    return checks, defects
