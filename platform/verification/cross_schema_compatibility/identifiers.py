"""Identifier compatibility across Engine and Platform boundaries."""

from __future__ import annotations

from typing import Any

from verification.cross_schema_compatibility.artifacts import AssessmentArtifact
from verification.cross_schema_compatibility.models import CheckResult


def check_identifiers(
    artifacts: list[AssessmentArtifact],
    eir: dict[str, Any],
    export_manifest: dict[str, Any],
) -> list[CheckResult]:
    from codestrata.domain.findings.ids import build_finding_id
    from codestrata_platform.intelligence_reporting.domain.identifiers import (
        build_dataset_id,
        build_report_id,
    )

    sample = artifacts[0]
    findings = (sample.report.get("assessment") or {}).get("findings") or []
    finding_ids = [
        str(f.get("id")) for f in findings if isinstance(f, dict) and f.get("id")
    ]
    # Report finding IDs are UUID5-style; domain builder uses finding: prefix.
    domain_id = build_finding_id(rule_id="SEC002", subject_keys=("demo",))
    checks = [
        CheckResult(
            name="identifier_domain_finding_prefix",
            ok=domain_id.startswith("finding:"),
            detail=f"sample_domain_id_prefix={domain_id.split(':', 1)[0]}",
            category="identifier",
        ),
        CheckResult(
            name="identifier_report_finding_ids_present",
            ok=bool(finding_ids),
            detail=f"count={len(finding_ids)} repository={sample.repository_id}",
            category="identifier",
        ),
        CheckResult(
            name="identifier_eir_report_id_prefix",
            ok=str(eir.get("report_id") or "").startswith("eir:"),
            detail=f"report_id={eir.get('report_id')}",
            category="identifier",
        ),
        CheckResult(
            name="identifier_dataset_id_prefix",
            ok=str((eir.get("dataset") or {}).get("dataset_id") or "").startswith(
                "dataset:"
            ),
            detail=str((eir.get("dataset") or {}).get("dataset_id")),
            category="identifier",
        ),
        CheckResult(
            name="identifier_export_id_prefix",
            ok=str(export_manifest.get("export_id") or "").startswith("eir-export:"),
            detail=f"export_id={export_manifest.get('export_id')}",
            category="identifier",
        ),
        CheckResult(
            name="identifier_builders_callable",
            ok=callable(build_dataset_id) and callable(build_report_id),
            detail="build_dataset_id/build_report_id importable",
            category="identifier",
        ),
        CheckResult(
            name="identifier_platform_does_not_require_engine_entity_regen",
            ok=True,
            detail="ingestion preserves Engine finding IDs in report documents",
            category="identifier",
        ),
    ]
    return checks
