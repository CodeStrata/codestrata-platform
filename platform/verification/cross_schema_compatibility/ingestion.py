"""Engine → Platform ingestion compatibility (customer-safe + identity)."""

from __future__ import annotations

from codestrata.security.customer_safe_text import ensure_customer_safe_report_document
from codestrata_platform.intelligence_reporting.application.contracts import (
    AssessmentDatasetInput,
    IntelligenceDatasetSelectionPolicy,
    SchemaCompatibilityPolicy,
    SUPPORTED_ASSESSMENT_SCHEMA_VERSION,
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

from verification.cross_schema_compatibility.artifacts import AssessmentArtifact
from verification.cross_schema_compatibility.models import (
    CheckResult,
    CompatibilityFailure,
)


def check_ingestion_sample(
    artifacts: list[AssessmentArtifact],
    *,
    sample_size: int = 3,
) -> tuple[list[CheckResult], list[CompatibilityFailure]]:
    """Ingest a small sample plus verify constants; full 22 covered by SV.12/SV.13."""

    checks: list[CheckResult] = []
    failures: list[CompatibilityFailure] = []
    checks.append(
        CheckResult(
            name="ingestion_supported_assessment_schema_1_2",
            ok=SUPPORTED_ASSESSMENT_SCHEMA_VERSION == "1.2",
            detail=f"SUPPORTED_ASSESSMENT_SCHEMA_VERSION={SUPPORTED_ASSESSMENT_SCHEMA_VERSION}",
            category="ingestion",
        )
    )
    sample = artifacts[:sample_size]
    source = InMemoryAssessmentReportSource()
    inputs: list[AssessmentDatasetInput] = []
    for item in sample:
        safe = ensure_customer_safe_report_document(item.report)
        ref = f"artifact:{item.repository_id}:sv14:report_json"
        source.put(ref, safe)
        inputs.append(
            AssessmentDatasetInput(
                repository_id=f"repo:{item.repository_id}",
                assessment_id=f"assessment:{item.repository_id}:sv14",
                assessment_run_id=f"run:{item.repository_id}:sv14",
                report_document=safe,
                report_reference=ref,
                source_type=SourceType.PUBLIC_OSS,
                visibility=DataVisibility.PUBLIC,
                pinned_revision="a" * 40,
                source_reference=f"https://github.com/example/{item.repository_id}",
                source_reference_publication_permitted=True,
                display_name=item.repository_id,
                explicitly_selected=True,
            )
        )
    result = ingest_assessment_dataset(
        inputs,
        name="sv14-ingestion-sample",
        policy=IntelligenceDatasetSelectionPolicy(
            schema_compatibility_policy=SchemaCompatibilityPolicy.REQUIRE_1_2_COMPLETE,
            require_pinned_revision_for_public_oss=True,
        ),
        report_source=source,
        dataset_tags=("sv14",),
    )
    included = len(result.included)
    rejected = len(result.rejected)
    ok = included == len(sample) and rejected == 0
    if not ok:
        failures.append(
            CompatibilityFailure(
                classification="projection",
                producer="Engine assessment",
                consumer="Platform EI ingestion",
                schema="assessment_report",
                field="dataset_inclusion",
                expected=f"included={len(sample)}",
                actual=f"included={included} rejected={rejected}",
            )
        )
    checks.append(
        CheckResult(
            name="ingestion_sample_accepted",
            ok=ok,
            detail=f"included={included} rejected={rejected} sample={len(sample)}",
            category="ingestion",
        )
    )
    return checks, failures
