"""Determinism verification for dataset/report identity and serialization."""

from __future__ import annotations

import json
from copy import deepcopy

from codestrata_platform.intelligence_reporting.domain.serialization import (
    from_stable_dict,
    report_to_stable_dict,
)
from codestrata_platform.intelligence_reporting.infrastructure.assessment_report_source import (
    InMemoryAssessmentReportSource,
)

from verification.engineering_intelligence.fixtures import make_public_input, synthetic_report
from verification.engineering_intelligence.ingestion import (
    PipelineArtifacts,
    build_pipeline_from_inputs,
)
from verification.engineering_intelligence.models import CheckResult


def _pipeline_from_order(order: list[tuple[str, str, str]]) -> PipelineArtifacts:
    inputs = []
    source = InMemoryAssessmentReportSource()
    for repo, assessment, run in order:
        report = synthetic_report(
            finding_id=f"finding:{repo}",
            evidence_id=f"ev:{repo}",
            recommendation_id=f"rec:{repo}",
            action_id=f"pa:{repo}",
            initiative_id=f"init:{repo}",
            rule_id="rule.shared",
        )
        item = make_public_input(
            repository_id=repo,
            assessment_id=assessment,
            assessment_run_id=run,
            report=report,
            pinned_revision="eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        )
        if item.report_reference and item.report_document is not None:
            source.put(item.report_reference, item.report_document)
        inputs.append(item)
    return build_pipeline_from_inputs(inputs, report_source=source, title="determinism")


def check_determinism(pipeline: PipelineArtifacts | None = None) -> list[CheckResult]:
    order_a = [
        ("repo:alpha", "assessment:alpha", "run:alpha"),
        ("repo:beta", "assessment:beta", "run:beta"),
    ]
    order_b = list(reversed(order_a))
    left = _pipeline_from_order(order_a)
    right = _pipeline_from_order(order_b)

    checks = [
        CheckResult(
            name="determinism:dataset_id_order_invariant",
            ok=left.report.dataset.dataset_id.value == right.report.dataset.dataset_id.value,
            detail=left.report.dataset.dataset_id.value,
            category="determinism",
            scenario="S",
        ),
        CheckResult(
            name="determinism:report_id_order_invariant",
            ok=left.report.report_id.value == right.report.report_id.value,
            detail=left.report.report_id.value,
            category="determinism",
            scenario="S",
        ),
        CheckResult(
            name="determinism:bundle_id_order_invariant",
            ok=left.report.interpretation_policy_bundle_id
            == right.report.interpretation_policy_bundle_id,
            detail=str(left.report.interpretation_policy_bundle_id)[:48],
            category="determinism",
            scenario="S",
        ),
    ]

    # Stable serialization round-trip
    payload = report_to_stable_dict(left.report)
    restored = from_stable_dict(payload)
    again = report_to_stable_dict(restored)
    checks.append(
        CheckResult(
            name="determinism:stable_serialization_roundtrip",
            ok=json.dumps(payload, sort_keys=True) == json.dumps(again, sort_keys=True),
            detail="round-trip equal",
            category="determinism",
            scenario="S",
        )
    )

    # Duplicate exact inputs do not change population
    report = synthetic_report()
    item = make_public_input(
        repository_id="repo:gamma",
        assessment_id="assessment:gamma",
        assessment_run_id="run:gamma",
        report=report,
        pinned_revision="ffffffffffffffffffffffffffffffffffffffff",
    )
    source = InMemoryAssessmentReportSource()
    source.put(item.report_reference, item.report_document)  # type: ignore[arg-type]
    single = build_pipeline_from_inputs([item], report_source=source, title="dup-pop")
    source2 = InMemoryAssessmentReportSource()
    source2.put(item.report_reference, deepcopy(item.report_document))  # type: ignore[arg-type]
    doubled = build_pipeline_from_inputs(
        [item, deepcopy(item)], report_source=source2, title="dup-pop"
    )
    checks.append(
        CheckResult(
            name="determinism:duplicate_input_population_stable",
            ok=single.report.dataset.repository_count == doubled.report.dataset.repository_count == 1,
            detail=f"single={single.report.dataset.repository_count} "
            f"double={doubled.report.dataset.repository_count}",
            category="determinism",
            scenario="D",
        )
    )

    if pipeline is not None:
        checks.append(
            CheckResult(
                name="determinism:primary_report_id_stable_prefix",
                ok=str(pipeline.report.report_id.value).startswith("eir:"),
                detail=pipeline.report.report_id.value,
                category="determinism",
            )
        )
    return checks
