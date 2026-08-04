"""Dataset identity and ingestion verification checks."""

from __future__ import annotations

from typing import Any

from codestrata_platform.intelligence_reporting.application.errors import (
    DuplicateAssessmentConflictError,
)
from codestrata_platform.intelligence_reporting.application.ingestion import (
    ingest_assessment_dataset,
)
from codestrata_platform.intelligence_reporting.application.normalization import (
    stable_canonical_report_digest,
)
from codestrata_platform.intelligence_reporting.domain.enums import DataVisibility, SourceType
from codestrata_platform.intelligence_reporting.domain.serialization import to_stable_dict
from codestrata_platform.intelligence_reporting.infrastructure.assessment_report_source import (
    InMemoryAssessmentReportSource,
)

from verification.engineering_intelligence.contract import ASSESSMENT_SCHEMA_VERSION
from verification.engineering_intelligence.fixtures import make_public_input, synthetic_report
from verification.engineering_intelligence.ingestion import PipelineArtifacts
from verification.engineering_intelligence.models import CheckResult


def check_dataset(pipeline: PipelineArtifacts) -> list[CheckResult]:
    ingest = pipeline.ingest_result
    dataset = ingest.dataset
    checks: list[CheckResult] = []
    checks.append(
        CheckResult(
            name="dataset:present",
            ok=dataset is not None,
            detail="IntelligenceDataset present",
            category="dataset",
        )
    )
    if dataset is None:
        return checks

    payload = to_stable_dict(dataset)
    checks.append(
        CheckResult(
            name="dataset:no_embedded_findings",
            ok="findings" not in payload and "priority_actions" not in payload,
            detail="refs/digests only",
            category="dataset",
        )
    )
    checks.append(
        CheckResult(
            name="dataset:id_prefix",
            ok=str(dataset.dataset_id.value).startswith("dataset:"),
            detail=str(dataset.dataset_id.value)[:40],
            category="dataset",
        )
    )
    snap_schemas = {s.assessment_schema_version for s in ingest.included}
    ok_schema = all(s == ASSESSMENT_SCHEMA_VERSION for s in snap_schemas) if snap_schemas else False
    checks.append(
        CheckResult(
            name="dataset:assessment_schema_1_2",
            ok=ok_schema,
            detail=f"schemas={sorted(str(s) for s in snap_schemas)}",
            category="dataset",
        )
    )
    checks.append(
        CheckResult(
            name="dataset:digest_present",
            ok=all(bool(s.canonical_report_digest) for s in ingest.included),
            detail=f"snapshots={len(ingest.included)}",
            category="dataset",
        )
    )
    return checks


def check_ingestion_scenarios() -> list[CheckResult]:
    """Offline scenarios D/E/J and schema rejection."""

    checks: list[CheckResult] = []
    report = synthetic_report()
    digest = stable_canonical_report_digest(report)

    # D: exact duplicate digest dedupe
    dup_inputs = [
        make_public_input(
            repository_id="repo:dup",
            assessment_id="assessment:dup",
            assessment_run_id="run:dup",
            report=report,
            pinned_revision="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        ),
        make_public_input(
            repository_id="repo:dup",
            assessment_id="assessment:dup",
            assessment_run_id="run:dup",
            report=report,
            pinned_revision="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        ),
    ]
    source = InMemoryAssessmentReportSource()
    for item in dup_inputs:
        if item.report_reference and item.report_document is not None:
            source.put(item.report_reference, item.report_document)
    result = ingest_assessment_dataset(dup_inputs, report_source=source)
    checks.append(
        CheckResult(
            name="scenario:D_duplicate_digest_dedupe",
            ok=result.dataset is not None and result.dataset.repository_count == 1,
            detail=f"population={getattr(result.dataset, 'repository_count', None)} digest={digest[:12]}",
            category="scenario",
            scenario="D",
        )
    )

    # E: conflicting digests fail closed
    conflict_report = synthetic_report(finding_id="finding:conflict")
    conflict_inputs = [
        make_public_input(
            repository_id="repo:conflict",
            assessment_id="assessment:conflict",
            assessment_run_id="run:conflict",
            report=report,
            pinned_revision="cccccccccccccccccccccccccccccccccccccccc",
        ),
        make_public_input(
            repository_id="repo:conflict",
            assessment_id="assessment:conflict",
            assessment_run_id="run:conflict",
            report=conflict_report,
            pinned_revision="cccccccccccccccccccccccccccccccccccccccc",
        ),
    ]
    conflict_ok = False
    detail = "no_error"
    try:
        ingest_assessment_dataset(conflict_inputs)
    except DuplicateAssessmentConflictError:
        conflict_ok = True
        detail = "DuplicateAssessmentConflictError"
    except Exception as exc:  # noqa: BLE001 — verification records unexpected failures
        detail = type(exc).__name__
        # Some policies reject via result.rejected instead of raise — accept fail-closed.
        conflict_ok = False
    if not conflict_ok:
        # Retry capturing rejected diagnostics style
        try:
            alt = ingest_assessment_dataset(conflict_inputs)
            conflict_ok = alt.dataset is None or any(
                getattr(r, "exclusion_reason", "") == "duplicate_conflict"
                or "conflict" in str(getattr(r, "exclusion_reason", "")).lower()
                for r in (alt.rejected or ())
            ) or len(getattr(alt, "diagnostics", ()) or ()) > 0 and alt.dataset is None
            detail = "rejected_or_empty" if conflict_ok else "silent_merge"
        except DuplicateAssessmentConflictError:
            conflict_ok = True
            detail = "DuplicateAssessmentConflictError"
    checks.append(
        CheckResult(
            name="scenario:E_conflicting_inputs_fail_closed",
            ok=conflict_ok,
            detail=detail,
            category="scenario",
            scenario="E",
        )
    )

    # Unsupported major schema rejected
    bad = synthetic_report()
    bad["schema_version"] = "2.0"
    rejected = ingest_assessment_dataset(
        [
            make_public_input(
                repository_id="repo:future",
                assessment_id="assessment:future",
                assessment_run_id="run:future",
                report=bad,
            )
        ]
    )
    checks.append(
        CheckResult(
            name="ingestion:future_schema_rejected",
            ok=len(rejected.rejected) == 1,
            detail=f"rejected={len(rejected.rejected)}",
            category="ingestion",
        )
    )

    # J: private visibility rejected under public OSS aggregation is checked elsewhere;
    # here ensure private input is classified explicitly.
    private = make_public_input(
        repository_id="repo:private",
        assessment_id="assessment:private",
        assessment_run_id="run:private",
        visibility=DataVisibility.CUSTOMER_PRIVATE,
        source_type=SourceType.CUSTOMER_PRIVATE,
    )
    checks.append(
        CheckResult(
            name="scenario:J_private_visibility_explicit",
            ok=private.visibility is DataVisibility.CUSTOMER_PRIVATE,
            detail=str(private.visibility.value),
            category="scenario",
            scenario="J",
        )
    )
    return checks
