"""Ingestion compatibility checks for previously rejected assessments."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from codestrata.security.customer_safe_text import ensure_customer_safe_report_document
from codestrata_platform.intelligence_reporting.application.contracts import (
    AssessmentDatasetInput,
    IntelligenceDatasetSelectionPolicy,
    SchemaCompatibilityPolicy,
)
from codestrata_platform.intelligence_reporting.application.ingestion import (
    ingest_assessment_dataset,
)
from codestrata_platform.intelligence_reporting.application.validation import (
    validate_report_document,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    DataVisibility,
    SourceType,
)
from codestrata_platform.intelligence_reporting.infrastructure.assessment_report_source import (
    InMemoryAssessmentReportSource,
)

from verification.engineering_intelligence.catalog import monorepo_root_from_here
from verification.system_defect_fixes.contract import (
    AFFECTED_REPOSITORY_IDS,
    SV10_OUTPUT_RELATIVE,
)
from verification.system_defect_fixes.models import CheckResult
from verification.system_defect_fixes.unsafe_metadata import (
    classify_description_shape,
    find_unsafe_customer_field_paths,
)


def _sv10_report(monorepo: Path, repository_id: str) -> tuple[Path, dict[str, Any]]:
    base = monorepo / SV10_OUTPUT_RELATIVE / "artifacts" / repository_id
    matches = sorted(base.glob("*/report.json"))
    if not matches:
        raise FileNotFoundError(f"missing SV.10 report for {repository_id}")
    path = matches[0]
    return path, json.loads(path.read_text(encoding="utf-8"))


def classify_affected_reports(
    monorepo: Path | None = None,
) -> list[dict[str, Any]]:
    """Document rejection causes without echoing unsafe values."""

    root = (monorepo or monorepo_root_from_here()).resolve()
    rows: list[dict[str, Any]] = []
    for repository_id in AFFECTED_REPOSITORY_IDS:
        _path, document = _sv10_report(root, repository_id)
        findings = (document.get("assessment") or {}).get("findings") or []
        unsafe_paths = find_unsafe_customer_field_paths(document)
        # Locate first finding whose description has PEM shape (safe label only).
        hit: dict[str, Any] | None = None
        for index, finding in enumerate(findings):
            if not isinstance(finding, dict):
                continue
            desc = finding.get("description")
            if not isinstance(desc, str):
                continue
            shape = classify_description_shape(desc)
            if shape != "no_pem_shape":
                hit = {
                    "finding_index": index,
                    "finding_id": finding.get("id"),
                    "rule_id": finding.get("rule_id"),
                    "title_present": bool(finding.get("title")),
                    "description_shape": shape,
                }
                break
        rows.append(
            {
                "repository_id": repository_id,
                "raw_unsafe_paths": unsafe_paths,
                "classification": "A_engine_unsafe_canonical_serialization",
                "finding": hit,
            }
        )
    return rows


def ingest_single_report(
    document: dict[str, Any],
    *,
    repository_id: str,
    pinned_revision: str = "0" * 40,
) -> tuple[int, int]:
    """Return (included, rejected) counts for one sanitized report."""

    safe = ensure_customer_safe_report_document(document)
    validate_report_document(safe)
    source = InMemoryAssessmentReportSource()
    ref = f"artifact:{repository_id}:sv13:report_json"
    source.put(ref, safe)
    result = ingest_assessment_dataset(
        [
            AssessmentDatasetInput(
                repository_id=f"repo:{repository_id}",
                assessment_id=f"assessment:{repository_id}:sv13",
                assessment_run_id=f"run:{repository_id}:sv13",
                report_document=safe,
                report_reference=ref,
                source_type=SourceType.PUBLIC_OSS,
                visibility=DataVisibility.PUBLIC,
                pinned_revision=pinned_revision,
                source_reference=f"https://github.com/example/{repository_id}",
                source_reference_publication_permitted=True,
                display_name=repository_id,
                explicitly_selected=True,
            )
        ],
        name=f"sv13-{repository_id}",
        policy=IntelligenceDatasetSelectionPolicy(
            schema_compatibility_policy=SchemaCompatibilityPolicy.REQUIRE_1_2_COMPLETE,
            require_pinned_revision_for_public_oss=True,
        ),
        report_source=source,
        dataset_tags=("sv13",),
    )
    return len(result.included), len(result.rejected)


def check_three_repository_ingestion(
    monorepo: Path | None = None,
) -> list[CheckResult]:
    root = (monorepo or monorepo_root_from_here()).resolve()
    checks: list[CheckResult] = []
    for repository_id in AFFECTED_REPOSITORY_IDS:
        _path, document = _sv10_report(root, repository_id)
        # Preserve finding identity while sanitizing presentation text.
        before_ids = [
            f.get("id")
            for f in (document.get("assessment") or {}).get("findings") or []
            if isinstance(f, dict)
        ]
        safe = ensure_customer_safe_report_document(document)
        after_ids = [
            f.get("id")
            for f in (safe.get("assessment") or {}).get("findings") or []
            if isinstance(f, dict)
        ]
        included, rejected = ingest_single_report(
            document,
            repository_id=repository_id,
            pinned_revision="a" * 40,
        )
        ok = (
            included == 1
            and rejected == 0
            and before_ids == after_ids
            and not find_unsafe_customer_field_paths(safe)
        )
        checks.append(
            CheckResult(
                name=f"ingest_{repository_id}",
                ok=ok,
                detail=f"included={included} rejected={rejected} ids_stable={before_ids == after_ids}",
            )
        )
    return checks
