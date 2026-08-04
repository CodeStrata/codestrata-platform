"""Privacy-safe models for SV.6 verification reports."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from verification.engineering_intelligence.contract import (
    ENGINEERING_INTELLIGENCE_VERIFICATION_ID,
    ENGINEERING_INTELLIGENCE_VERIFICATION_VERSION,
)


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    ok: bool
    detail: str = ""
    category: str = "structural"
    scenario: str = ""


@dataclass(frozen=True, slots=True)
class RepositoryInputRecord:
    repository_id: str
    github_repository: str | None
    qualified_revision: str
    source_tag: str | None
    language_group: str
    assessment_run_reference: str
    report_digest: str
    schema_version: str
    source: str  # catalog_assess | cache | fixture


@dataclass(frozen=True, slots=True)
class PipelineVerification:
    ok: bool
    catalog_id: str
    repository_ids: tuple[str, ...]
    repository_inputs: tuple[RepositoryInputRecord, ...]
    dataset_id: str | None
    aggregation_id: str | None
    report_id: str | None
    interpretation_policy_bundle_id: str | None
    repository_population: dict[str, int] = field(default_factory=dict)
    section_population: dict[str, int] = field(default_factory=dict)
    eir_schema_version: str | None = None
    ingestion_checks: tuple[CheckResult, ...] = ()
    dataset_checks: tuple[CheckResult, ...] = ()
    aggregation_checks: tuple[CheckResult, ...] = ()
    technology_checks: tuple[CheckResult, ...] = ()
    capability_checks: tuple[CheckResult, ...] = ()
    pattern_checks: tuple[CheckResult, ...] = ()
    modernization_checks: tuple[CheckResult, ...] = ()
    report_quality_checks: tuple[CheckResult, ...] = ()
    drilldown_checks: tuple[CheckResult, ...] = ()
    provenance_checks: tuple[CheckResult, ...] = ()
    determinism_checks: tuple[CheckResult, ...] = ()
    safety_checks: tuple[CheckResult, ...] = ()
    scenario_checks: tuple[CheckResult, ...] = ()
    failures: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class VerificationReport:
    schema_name: str = ENGINEERING_INTELLIGENCE_VERIFICATION_ID
    schema_version: str = ENGINEERING_INTELLIGENCE_VERIFICATION_VERSION
    verification_id: str = ENGINEERING_INTELLIGENCE_VERIFICATION_ID
    ok: bool = False
    verdict: str = "fail"
    catalog_id: str | None = None
    pipeline: PipelineVerification | None = None
    defects: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    elapsed_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        def checks(items: tuple[CheckResult, ...]) -> list[dict[str, Any]]:
            return [asdict(item) for item in items]

        pipeline_payload: dict[str, Any] | None = None
        if self.pipeline is not None:
            p = self.pipeline
            pipeline_payload = {
                "ok": p.ok,
                "catalog_id": p.catalog_id,
                "repository_ids": list(p.repository_ids),
                "repository_inputs": [asdict(item) for item in p.repository_inputs],
                "dataset_id": p.dataset_id,
                "aggregation_id": p.aggregation_id,
                "report_id": p.report_id,
                "interpretation_policy_bundle_id": p.interpretation_policy_bundle_id,
                "repository_population": p.repository_population,
                "section_population": p.section_population,
                "eir_schema_version": p.eir_schema_version,
                "ingestion_checks": checks(p.ingestion_checks),
                "dataset_checks": checks(p.dataset_checks),
                "aggregation_checks": checks(p.aggregation_checks),
                "technology_checks": checks(p.technology_checks),
                "capability_checks": checks(p.capability_checks),
                "pattern_checks": checks(p.pattern_checks),
                "modernization_checks": checks(p.modernization_checks),
                "report_quality_checks": checks(p.report_quality_checks),
                "drilldown_checks": checks(p.drilldown_checks),
                "provenance_checks": checks(p.provenance_checks),
                "determinism_checks": checks(p.determinism_checks),
                "safety_checks": checks(p.safety_checks),
                "scenario_checks": checks(p.scenario_checks),
                "failures": list(p.failures),
                "warnings": list(p.warnings),
                "limitations": list(p.limitations),
            }
        return {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "verification_id": self.verification_id,
            "ok": self.ok,
            "verdict": self.verdict,
            "catalog_id": self.catalog_id,
            "pipeline": pipeline_payload,
            "defects": list(self.defects),
            "warnings": list(self.warnings),
            "limitations": list(self.limitations),
            "elapsed_ms": self.elapsed_ms,
        }

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
