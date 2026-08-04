"""Load the verified SV.6 five-repository EngineeringIntelligenceReport."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from codestrata_platform.intelligence_reporting.application.website_export import (
    WebsiteExportBuildPolicy,
    WebsiteExportBundle,
    build_website_safe_export,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION,
    EngineeringIntelligenceReport,
)

from verification.engineering_intelligence.assessment_inputs import (
    prepare_catalog_assessments,
)
from verification.engineering_intelligence.catalog import monorepo_root_from_here
from verification.engineering_intelligence.contract import PREFERRED_FIVE_LANGUAGE_SUBSET
from verification.engineering_intelligence.ingestion import (
    PipelineArtifacts,
    build_pipeline_from_assessments,
)
from verification.website_export.contract import (
    EXPECTED_SV6_DATASET_ID,
    EXPECTED_SV6_INTERP_BUNDLE,
    EXPECTED_SV6_REPORT_ID,
)
from verification.website_export.models import CheckResult


DEFAULT_CACHE_RELATIVE = Path(
    "platform/reports/verification/engineering-intelligence-assessments"
)


@dataclass(frozen=True, slots=True)
class VerifiedExportInput:
    pipeline: PipelineArtifacts
    report: EngineeringIntelligenceReport
    policy: WebsiteExportBuildPolicy
    bundle: WebsiteExportBundle


def default_cache_dir(monorepo: Path | None = None) -> Path:
    root = (monorepo or monorepo_root_from_here()).resolve()
    return (root / DEFAULT_CACHE_RELATIVE).resolve()


def load_verified_five_repo_pipeline(
    *,
    monorepo: Path | None = None,
    cache_dir: Path | None = None,
    with_catalog_network: bool = False,
) -> PipelineArtifacts:
    root = (monorepo or monorepo_root_from_here()).resolve()
    work = (cache_dir or default_cache_dir(root)).resolve()
    assessments, _catalog, _work = prepare_catalog_assessments(
        monorepo=root,
        work_root=work,
        repository_ids=PREFERRED_FIVE_LANGUAGE_SUBSET,
        with_catalog_network=with_catalog_network,
        reuse_cache=True,
    )
    return build_pipeline_from_assessments(
        assessments,
        title="SV.6 Five-Language Engineering Intelligence Verification",
    )


def verify_source_eir(report: EngineeringIntelligenceReport) -> list[CheckResult]:
    checks: list[CheckResult] = []
    checks.append(
        CheckResult(
            name="input:report_id",
            ok=report.report_id.value == EXPECTED_SV6_REPORT_ID,
            detail=report.report_id.value,
            category="inputs",
        )
    )
    checks.append(
        CheckResult(
            name="input:dataset_id",
            ok=report.dataset.dataset_id.value == EXPECTED_SV6_DATASET_ID,
            detail=report.dataset.dataset_id.value,
            category="inputs",
        )
    )
    checks.append(
        CheckResult(
            name="input:interp_bundle",
            ok=report.interpretation_policy_bundle_id == EXPECTED_SV6_INTERP_BUNDLE,
            detail=report.interpretation_policy_bundle_id,
            category="inputs",
        )
    )
    checks.append(
        CheckResult(
            name="input:schema_1_0",
            ok=ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION == "1.0"
            and report.schema_version == "1.0",
            detail=report.schema_version,
            category="inputs",
        )
    )
    checks.append(
        CheckResult(
            name="input:five_repositories",
            ok=len(report.dataset.included_repository_ids) == 5,
            detail=f"count={len(report.dataset.included_repository_ids)}",
            category="inputs",
            scenario="A",
        )
    )
    checks.append(
        CheckResult(
            name="input:five_drilldowns",
            ok=len(report.repository_drilldowns) == 5,
            detail=f"count={len(report.repository_drilldowns)}",
            category="inputs",
            scenario="A",
        )
    )
    checks.append(
        CheckResult(
            name="input:public_oss_scope",
            ok=report.report_scope.value == "public_oss_dataset",
            detail=report.report_scope.value,
            category="inputs",
            scenario="A",
        )
    )
    checks.append(
        CheckResult(
            name="input:confidence_present",
            ok=report.confidence is not None,
            detail=str(getattr(report.confidence, "level", None)),
            category="inputs",
        )
    )
    checks.append(
        CheckResult(
            name="input:limitations_present",
            ok=bool(report.limitations),
            detail=f"count={len(report.limitations)}",
            category="inputs",
        )
    )
    return checks


def build_verified_export(
    *,
    monorepo: Path | None = None,
    cache_dir: Path | None = None,
    with_catalog_network: bool = False,
    generated_at: str | None = None,
) -> VerifiedExportInput:
    pipeline = load_verified_five_repo_pipeline(
        monorepo=monorepo,
        cache_dir=cache_dir,
        with_catalog_network=with_catalog_network,
    )
    report = pipeline.report
    policy = WebsiteExportBuildPolicy.for_report_scope(report.report_scope)
    bundle = build_website_safe_export(
        report, policy=policy, generated_at=generated_at
    )
    return VerifiedExportInput(
        pipeline=pipeline,
        report=report,
        policy=policy,
        bundle=bundle,
    )
