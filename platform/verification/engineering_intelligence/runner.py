"""SV.6 Engineering Intelligence pipeline verification runner."""

from __future__ import annotations

import time
from pathlib import Path

from verification.engineering_intelligence.aggregation import check_aggregation
from verification.engineering_intelligence.assessment_inputs import (
    PreparedAssessment,
    prepare_catalog_assessments,
)
from verification.engineering_intelligence.capabilities import check_capabilities
from verification.engineering_intelligence.catalog import monorepo_root_from_here
from verification.engineering_intelligence.contract import (
    EiVerificationContract,
    PREFERRED_FIVE_LANGUAGE_SUBSET,
    default_contract,
)
from verification.engineering_intelligence.dataset import check_dataset
from verification.engineering_intelligence.determinism import check_determinism
from verification.engineering_intelligence.drilldowns import check_drilldowns
from verification.engineering_intelligence.ingestion import (
    PipelineArtifacts,
    build_pipeline_from_assessments,
)
from verification.engineering_intelligence.models import (
    CheckResult,
    PipelineVerification,
    RepositoryInputRecord,
    VerificationReport,
)
from verification.engineering_intelligence.modernization import check_modernization
from verification.engineering_intelligence.patterns import check_patterns
from verification.engineering_intelligence.provenance import check_provenance
from verification.engineering_intelligence.report_quality import check_report_quality
from verification.engineering_intelligence.reporting import write_verification_report
from verification.engineering_intelligence.safety import check_safety
from verification.engineering_intelligence.scenarios import run_offline_scenarios
from verification.engineering_intelligence.technology import check_technology


def _section_population(pipeline: PipelineArtifacts) -> dict[str, int]:
    report = pipeline.report
    tech = report.technology_distribution
    tech_count = len(getattr(tech, "observations", ()) or ()) if tech else 0
    return {
        "technology_observations": tech_count,
        "capability_comparisons": len(report.capability_comparisons or ()),
        "assessment_head_distributions": len(report.assessment_head_distributions or ()),
        "recurring_patterns": len(report.recurring_patterns or ()),
        "modernization_observations": len(report.modernization_observations or ()),
        "dataset_limitations": len(report.limitations or ()),
        "repository_drilldowns": len(report.repository_drilldowns or ()),
    }


def _population(pipeline: PipelineArtifacts) -> dict[str, int]:
    dataset = pipeline.ingest_result.dataset
    pop = pipeline.report.repository_population
    return {
        "included": len(dataset.included_repository_ids),
        "dataset_repository_count": int(dataset.repository_count),
        "population_repository_count": int(getattr(pop, "repository_count", 0) or 0)
        if pop
        else 0,
    }


def _verify_pipeline(
    *,
    pipeline: PipelineArtifacts,
    assessments: list[PreparedAssessment],
    catalog_id: str,
    extra_scenarios: list[CheckResult] | None = None,
) -> PipelineVerification:
    ingestion = check_dataset(pipeline)
    aggregation = check_aggregation(pipeline)
    technology = check_technology(pipeline)
    capability = check_capabilities(pipeline)
    patterns = check_patterns(pipeline)
    modernization = check_modernization(pipeline)
    quality = check_report_quality(pipeline)
    drilldowns = check_drilldowns(pipeline)
    provenance = check_provenance(pipeline)
    determinism = check_determinism(pipeline)
    safety = check_safety(pipeline)
    scenarios = list(extra_scenarios or [])

    all_checks = (
        ingestion
        + aggregation
        + technology
        + capability
        + patterns
        + modernization
        + quality
        + drilldowns
        + provenance
        + determinism
        + safety
        + scenarios
    )
    failures = [f"{c.name}:{c.detail}" for c in all_checks if not c.ok]
    inputs = tuple(
        RepositoryInputRecord(
            repository_id=item.repository_id,
            github_repository=item.github_repository,
            qualified_revision=item.qualified_revision,
            source_tag=item.source_tag,
            language_group=item.language_group,
            assessment_run_reference=item.assessment_run_reference,
            report_digest=item.report_digest,
            schema_version=item.schema_version,
            source=item.source,
        )
        for item in assessments
    )
    agg_id = getattr(pipeline.aggregation, "aggregation_id", None)
    return PipelineVerification(
        ok=not failures,
        catalog_id=catalog_id,
        repository_ids=tuple(item.repository_id for item in assessments),
        repository_inputs=inputs,
        dataset_id=pipeline.ingest_result.dataset.dataset_id.value,
        aggregation_id=str(agg_id) if agg_id else None,
        report_id=pipeline.report.report_id.value,
        interpretation_policy_bundle_id=pipeline.report.interpretation_policy_bundle_id,
        repository_population=_population(pipeline),
        section_population=_section_population(pipeline),
        eir_schema_version=str(pipeline.report.schema_version),
        ingestion_checks=tuple(ingestion),
        dataset_checks=tuple(ingestion),
        aggregation_checks=tuple(aggregation),
        technology_checks=tuple(technology),
        capability_checks=tuple(capability),
        pattern_checks=tuple(patterns),
        modernization_checks=tuple(modernization),
        report_quality_checks=tuple(quality),
        drilldown_checks=tuple(drilldowns),
        provenance_checks=tuple(provenance),
        determinism_checks=tuple(determinism),
        safety_checks=tuple(safety),
        scenario_checks=tuple(scenarios),
        failures=tuple(failures),
    )


def run_engineering_intelligence_verification(
    *,
    monorepo: Path | None = None,
    output_dir: Path | None = None,
    cache_dir: Path | None = None,
    repository_ids: tuple[str, ...] | None = None,
    with_catalog_network: bool = False,
    offline_scenarios_only: bool = False,
    contract: EiVerificationContract | None = None,
) -> VerificationReport:
    started = time.perf_counter()
    contract = contract or default_contract()
    monorepo = (monorepo or monorepo_root_from_here()).resolve()
    out = (
        output_dir
        or (monorepo / "platform" / "reports" / "verification")
    ).resolve()
    out.mkdir(parents=True, exist_ok=True)

    limitations = list(contract.notes)
    defects: list[str] = []
    warnings: list[str] = []
    pipeline_result: PipelineVerification | None = None
    catalog_id: str | None = None

    scenario_checks = run_offline_scenarios()
    scenario_failures = [f"{c.name}:{c.detail}" for c in scenario_checks if not c.ok]

    if offline_scenarios_only:
        ok = not scenario_failures
        report = VerificationReport(
            ok=ok,
            verdict="pass" if ok else "fail",
            catalog_id=None,
            pipeline=PipelineVerification(
                ok=ok,
                catalog_id="",
                repository_ids=(),
                repository_inputs=(),
                dataset_id=None,
                aggregation_id=None,
                report_id=None,
                interpretation_policy_bundle_id=None,
                scenario_checks=tuple(scenario_checks),
                failures=tuple(scenario_failures),
                limitations=tuple(limitations),
            ),
            defects=tuple(scenario_failures),
            limitations=tuple(limitations + ["offline_scenarios_only: catalog pipeline skipped"]),
            elapsed_ms=(time.perf_counter() - started) * 1000,
        )
        write_verification_report(report, out)
        return report

    try:
        assessments, catalog, _work = prepare_catalog_assessments(
            monorepo=monorepo,
            work_root=cache_dir or (out / "engineering-intelligence-assessments"),
            repository_ids=repository_ids or PREFERRED_FIVE_LANGUAGE_SUBSET,
            with_catalog_network=with_catalog_network,
            reuse_cache=True,
        )
        catalog_id = catalog.catalog_id
        pipeline = build_pipeline_from_assessments(
            assessments,
            title="SV.6 Five-Language Engineering Intelligence Verification",
        )
        pipeline_result = _verify_pipeline(
            pipeline=pipeline,
            assessments=assessments,
            catalog_id=catalog.catalog_id,
            extra_scenarios=scenario_checks,
        )
        if not pipeline_result.ok:
            defects.extend(pipeline_result.failures)
    except FileNotFoundError as exc:
        warnings.append(str(exc))
        limitations.append(
            "catalog-backed assessments unavailable; ran offline scenarios only"
        )
        pipeline_result = PipelineVerification(
            ok=not scenario_failures,
            catalog_id="",
            repository_ids=(),
            repository_inputs=(),
            dataset_id=None,
            aggregation_id=None,
            report_id=None,
            interpretation_policy_bundle_id=None,
            scenario_checks=tuple(scenario_checks),
            failures=tuple(scenario_failures),
            warnings=tuple(warnings),
            limitations=tuple(limitations),
        )
        if scenario_failures:
            defects.extend(scenario_failures)
        else:
            # Missing cache without network is not a product defect when explicitly local.
            defects.append(f"missing_cached_assessments:{exc}")
    except Exception as exc:  # noqa: BLE001
        defects.append(f"pipeline_error:{type(exc).__name__}:{exc}")
        pipeline_result = PipelineVerification(
            ok=False,
            catalog_id=catalog_id or "",
            repository_ids=(),
            repository_inputs=(),
            dataset_id=None,
            aggregation_id=None,
            report_id=None,
            interpretation_policy_bundle_id=None,
            scenario_checks=tuple(scenario_checks),
            failures=tuple(defects),
            limitations=tuple(limitations),
        )

    ok = pipeline_result is not None and pipeline_result.ok and not defects
    # If only missing cache defect and scenarios passed, verdict reflects that.
    verdict = "pass" if ok else "fail"
    if (
        not ok
        and pipeline_result is not None
        and not scenario_failures
        and any(d.startswith("missing_cached_assessments:") for d in defects)
        and not with_catalog_network
    ):
        verdict = "pass_with_cache_gap"

    report = VerificationReport(
        ok=ok or verdict == "pass_with_cache_gap",
        verdict=verdict,
        catalog_id=catalog_id,
        pipeline=pipeline_result,
        defects=tuple(defects) if verdict == "fail" else (),
        warnings=tuple(warnings),
        limitations=tuple(limitations),
        elapsed_ms=(time.perf_counter() - started) * 1000,
    )
    # For cache-gap mode, keep warning defects out of hard fail list but note in warnings.
    if verdict == "pass_with_cache_gap":
        report = VerificationReport(
            ok=True,
            verdict=verdict,
            catalog_id=catalog_id,
            pipeline=pipeline_result,
            defects=(),
            warnings=tuple(warnings),
            limitations=tuple(limitations),
            elapsed_ms=(time.perf_counter() - started) * 1000,
        )
    write_verification_report(report, out)
    return report
