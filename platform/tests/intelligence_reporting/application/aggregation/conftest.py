"""Fixtures for cross-repository aggregation tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from codestrata_platform.intelligence_reporting.application.aggregation import (
    IntelligenceAggregationPolicy,
    aggregate_intelligence_dataset,
)
from codestrata_platform.intelligence_reporting.application.contracts import (
    AssessmentDatasetInput,
)
from codestrata_platform.intelligence_reporting.application.ingestion import (
    ingest_assessment_dataset,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    DataVisibility,
    SourceType,
)
from codestrata_platform.intelligence_reporting.infrastructure.assessment_report_source import (
    InMemoryAssessmentReportSource,
)
from tests.intelligence_reporting.application.conftest import full_engine_report


def prepare_aggregation(
    *,
    repos: list[tuple[str, str, str, dict[str, Any]]] | None = None,
    policy: IntelligenceAggregationPolicy | None = None,
    visibility: DataVisibility = DataVisibility.ANONYMIZED,
    source_type: SourceType = SourceType.PUBLIC_OSS,
):
    """Ingest fixtures into a dataset + report source ready for aggregation."""

    if repos is None:
        repos = [
            ("repo:one", "assessment:one", "run:one", full_engine_report()),
            (
                "repo:two",
                "assessment:two",
                "run:two",
                full_engine_report(
                    finding_id="finding:2",
                    evidence_id="ev:beta",
                    recommendation_id="rec:2",
                    action_id="pa:2",
                    initiative_id="init:2",
                ),
            ),
        ]
    source = InMemoryAssessmentReportSource()
    inputs: list[AssessmentDatasetInput] = []
    for repository_id, assessment_id, run_id, report in repos:
        ref = f"artifact:{assessment_id}:report_json"
        doc = deepcopy(report)
        source.put(ref, doc)
        inputs.append(
            AssessmentDatasetInput(
                repository_id=repository_id,
                assessment_id=assessment_id,
                assessment_run_id=run_id,
                report_document=doc,
                report_reference=ref,
                source_type=source_type,
                visibility=visibility,
                pinned_revision="abc123def",
                source_reference=(
                    f"https://github.com/example/{repository_id.split(':', 1)[-1]}"
                    if visibility is DataVisibility.PUBLIC
                    else None
                ),
                source_reference_publication_permitted=visibility is DataVisibility.PUBLIC,
            )
        )
    result = ingest_assessment_dataset(inputs)
    assert result.dataset is not None
    aggregation = aggregate_intelligence_dataset(
        dataset=result.dataset,
        snapshots=result.included,
        report_source=source,
        policy=policy,
        comparability=result.comparability,
    )
    return result, aggregation, source
