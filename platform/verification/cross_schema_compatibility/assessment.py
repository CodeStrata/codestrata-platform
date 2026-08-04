"""Assessment schema 1.2 compatibility across 22 preserved reports."""

from __future__ import annotations

from typing import Any

from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION
from codestrata.security.customer_safe_text import ensure_customer_safe_report_document
from codestrata_platform.intelligence_reporting.application.errors import (
    UnsafeAssessmentMetadataError,
)
from codestrata_platform.intelligence_reporting.application.validation import (
    validate_report_document,
)

from verification.cross_schema_compatibility.artifacts import AssessmentArtifact
from verification.cross_schema_compatibility.contract import TARGET_REPOSITORY_COUNT
from verification.cross_schema_compatibility.models import (
    CheckResult,
    CompatibilityFailure,
)


def _finding_ids(doc: Any) -> list[str]:
    if isinstance(doc, dict):
        items = doc.get("findings") or doc.get("items") or []
        if not items and "assessment" in doc:
            return _finding_ids(doc.get("assessment"))
    elif isinstance(doc, list):
        items = doc
    else:
        return []
    return [str(f.get("id")) for f in items if isinstance(f, dict) and f.get("id")]


def check_assessment_artifacts(
    artifacts: list[AssessmentArtifact],
) -> tuple[list[CheckResult], list[CompatibilityFailure]]:
    checks: list[CheckResult] = []
    failures: list[CompatibilityFailure] = []

    checks.append(
        CheckResult(
            name="assessment_artifact_count_22",
            ok=len(artifacts) == TARGET_REPOSITORY_COUNT,
            detail=f"count={len(artifacts)}",
            category="assessment",
        )
    )
    checks.append(
        CheckResult(
            name="assessment_product_constant_1_2",
            ok=ASSESSMENT_JSON_SCHEMA_VERSION == "1.2",
            detail=f"ASSESSMENT_JSON_SCHEMA_VERSION={ASSESSMENT_JSON_SCHEMA_VERSION}",
            category="assessment",
        )
    )

    schema_ok = 0
    platform_ok = 0
    companion_ok = 0
    id_stable = 0

    for item in artifacts:
        schema = str(item.report.get("schema_version") or "")
        if schema == ASSESSMENT_JSON_SCHEMA_VERSION:
            schema_ok += 1
        else:
            failures.append(
                CompatibilityFailure(
                    classification="version_contract",
                    producer="Engine assessment reporting",
                    consumer="SV.14 assessment check",
                    schema="assessment_report",
                    field="schema_version",
                    expected="1.2",
                    actual=schema or "<missing>",
                    detail=f"repository={item.repository_id}",
                )
            )

        raw_ids = _finding_ids(item.report.get("assessment") or {})
        safe = ensure_customer_safe_report_document(item.report)
        safe_ids = _finding_ids(safe.get("assessment") or {})
        if raw_ids == safe_ids:
            id_stable += 1

        try:
            validate_report_document(safe)
            platform_ok += 1
        except UnsafeAssessmentMetadataError:
            failures.append(
                CompatibilityFailure(
                    classification="privacy",
                    producer="Engine customer-safe projection",
                    consumer="Platform validate_report_document",
                    schema="assessment_report",
                    field="customer_facing_strings",
                    expected="accepted after customer-safe projection",
                    actual="unsafe_metadata",
                    detail=f"repository={item.repository_id}",
                )
            )

        if item.findings is not None:
            companion_ids = set(_finding_ids(item.findings))
            report_ids = set(raw_ids)
            # Companion may be a subset or equal; require no orphan companion IDs.
            if companion_ids <= report_ids or companion_ids == report_ids:
                companion_ok += 1
            else:
                failures.append(
                    CompatibilityFailure(
                        classification="identifier",
                        producer="findings.json",
                        consumer="report.json",
                        schema="findings_companion",
                        field="finding.id",
                        expected="subset_of_report_findings",
                        actual="orphan_companion_ids",
                        detail=f"repository={item.repository_id}",
                    )
                )
        else:
            companion_ok += 1  # optional absence tolerated for this check count

    checks.extend(
        [
            CheckResult(
                name="assessment_schema_version_all_1_2",
                ok=schema_ok == len(artifacts),
                detail=f"{schema_ok}/{len(artifacts)}",
                category="assessment",
            ),
            CheckResult(
                name="assessment_platform_ingestion_safety",
                ok=platform_ok == len(artifacts),
                detail=f"{platform_ok}/{len(artifacts)} after customer-safe projection",
                category="assessment",
            ),
            CheckResult(
                name="assessment_finding_ids_stable_under_safe_projection",
                ok=id_stable == len(artifacts),
                detail=f"{id_stable}/{len(artifacts)}",
                category="identifier",
            ),
            CheckResult(
                name="assessment_findings_companion_reconcile",
                ok=companion_ok == len(artifacts),
                detail=f"{companion_ok}/{len(artifacts)}",
                category="assessment",
            ),
        ]
    )
    return checks, failures
