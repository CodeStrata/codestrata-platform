"""Derive IntelligenceReportConfidence via weakest-material-support + caps."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.report_quality.comparability import (
    ComparabilitySummary,
)
from codestrata_platform.intelligence_reporting.application.report_quality.coverage import (
    DatasetCoverageSummary,
    material_snapshots,
)
from codestrata_platform.intelligence_reporting.application.report_quality.policy import (
    ReportQualityPolicy,
)
from codestrata_platform.intelligence_reporting.domain.confidence import (
    IntelligenceReportConfidence,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ComparabilityStatus,
    ConfidenceLevel,
    CoverageStatus,
    DerivationStatus,
    LimitationSeverity,
)
from codestrata_platform.intelligence_reporting.domain.limitations import DatasetLimitation
from codestrata_platform.intelligence_reporting.domain.report import (
    EngineeringIntelligenceReport,
)

_LEVEL_RANK = {
    ConfidenceLevel.UNAVAILABLE: 0,
    ConfidenceLevel.LIMITED: 1,
    ConfidenceLevel.MODERATE: 2,
    ConfidenceLevel.HIGH: 3,
}


def _cap(current: ConfidenceLevel, ceiling: ConfidenceLevel) -> ConfidenceLevel:
    if _LEVEL_RANK[current] <= _LEVEL_RANK[ceiling]:
        return current
    return ceiling


def weakest_material_source_confidence(
    report: EngineeringIntelligenceReport,
) -> ConfidenceLevel:
    """Weakest contributing head confidence — never an average of ordinals."""

    levels: list[ConfidenceLevel] = []
    for comparison in report.capability_comparisons:
        snaps = material_snapshots(comparison)
        if not snaps:
            continue
        for snap in snaps:
            if snap.legacy_limited:
                levels.append(ConfidenceLevel.LIMITED)
                continue
            if snap.confidence_level is ConfidenceLevel.UNAVAILABLE:
                # Material coverage with unavailable head confidence caps support.
                levels.append(ConfidenceLevel.UNAVAILABLE)
                continue
            levels.append(snap.confidence_level)
    if not levels:
        # Fall back to technology observation confidence if capability empty.
        for obs in report.technology_distribution.observations:
            if obs.confidence is not ConfidenceLevel.UNAVAILABLE:
                levels.append(obs.confidence)
    if not levels:
        return ConfidenceLevel.UNAVAILABLE
    return min(levels, key=lambda level: _LEVEL_RANK[level])


def evaluate_material_sections(
    report: EngineeringIntelligenceReport,
    *,
    policy: ReportQualityPolicy,
    coverage: DatasetCoverageSummary,
) -> tuple[int, int, int, int, tuple[str, ...]]:
    """Return material_count, supported, unavailable, small_sample, basis tokens."""

    material = set(policy.material_sections)
    optional = set(policy.optional_sections)
    supported = 0
    unavailable = 0
    small_sample = 0
    basis: list[str] = []
    counted = 0

    def count_material(name: str, *, ok: bool, unavailable_flag: bool = False) -> None:
        nonlocal supported, unavailable, counted
        if name not in material:
            return
        counted += 1
        if unavailable_flag:
            unavailable += 1
        elif ok:
            supported += 1

    if "dataset" in material:
        count_material("dataset", ok=report.dataset.repository_count > 0, unavailable_flag=report.dataset.repository_count == 0)
        if report.dataset.repository_count > 0:
            basis.append("canonical_assessment_sources")

    if "repository_population" in material:
        pop_ok = report.repository_population.repository_count > 0
        count_material(
            "repository_population",
            ok=pop_ok,
            unavailable_flag=not pop_ok,
        )

    if "technology_distribution" in material:
        denom = report.technology_distribution.repository_denominator
        if denom == 0 and report.dataset.repository_count > 0:
            count_material("technology_distribution", ok=False, unavailable_flag=True)
            basis.append("partial_section_denominators")
        else:
            count_material("technology_distribution", ok=denom > 0 or report.dataset.repository_count == 0)
            if denom > 0:
                basis.append("complete_section_denominators")

    if "capability_comparison" in material:
        if not report.capability_comparisons:
            count_material("capability_comparison", ok=False, unavailable_flag=True)
            basis.append("section_support_partial")
        else:
            partial = coverage.status in {
                CoverageStatus.PARTIAL,
                CoverageStatus.INSUFFICIENT_EVIDENCE,
            }
            unavailable_cov = coverage.status is CoverageStatus.UNAVAILABLE
            count_material(
                "capability_comparison",
                ok=not unavailable_cov,
                unavailable_flag=unavailable_cov,
            )
            if partial:
                basis.append("mixed_assessment_coverage")
            elif coverage.status is CoverageStatus.COMPLETE:
                basis.append("section_support_complete")

    if "assessment_head_distribution" in material:
        if not report.assessment_head_distributions:
            # Empty when capability empty — already counted via capability.
            if "capability_comparison" not in material:
                count_material(
                    "assessment_head_distribution",
                    ok=False,
                    unavailable_flag=True,
                )
            else:
                # Count once with capability; mark supported if heads exist.
                pass
        else:
            count_material("assessment_head_distribution", ok=True)
            for head in report.assessment_head_distributions:
                if 0 < head.repository_count < policy.small_sample_threshold:
                    small_sample += 1

    # Optional sections: empty is honest, not a confidence failure.
    if "recurring_patterns" in optional:
        if report.recurring_patterns:
            basis.append("comparable_repository_sample")
            for pattern in report.recurring_patterns:
                if len(pattern.repository_ids) < policy.small_sample_threshold:
                    small_sample += 1
    if "modernization_observations" in optional:
        if report.modernization_observations:
            for observation in report.modernization_observations:
                if len(observation.repository_ids) < policy.small_sample_threshold:
                    small_sample += 1

    return counted, supported, unavailable, small_sample, tuple(sorted(set(basis)))


def derive_report_confidence(
    report: EngineeringIntelligenceReport,
    *,
    policy: ReportQualityPolicy,
    coverage: DatasetCoverageSummary,
    comparability: ComparabilitySummary,
    limitations: tuple[DatasetLimitation, ...],
) -> IntelligenceReportConfidence:
    """Derive report confidence without averaging or percentages."""

    basis: set[str] = set()
    level = ConfidenceLevel.HIGH
    weakest = weakest_material_source_confidence(report)

    (
        material_count,
        supported_material,
        unavailable_material,
        small_sample_sections,
        section_basis,
    ) = evaluate_material_sections(report, policy=policy, coverage=coverage)
    basis.update(section_basis)

    included = comparability.included_repository_count
    comparable = comparability.comparable_repository_count

    if included == 0 or comparable == 0:
        level = ConfidenceLevel.UNAVAILABLE
        basis.add("small_repository_sample")
    elif included == 1:
        level = _cap(level, ConfidenceLevel.LIMITED)
        basis.add("small_repository_sample")
    elif included < policy.minimum_repository_count:
        level = _cap(level, ConfidenceLevel.LIMITED)
        basis.add("small_repository_sample")
    elif included < policy.small_sample_threshold:
        level = _cap(level, ConfidenceLevel.MODERATE)
        basis.add("small_repository_sample")
    else:
        basis.add("comparable_repository_sample")

    if comparable < policy.minimum_comparable_repository_count and included > 0:
        level = _cap(level, ConfidenceLevel.LIMITED)
        basis.add("small_repository_sample")

    if unavailable_material > 0:
        level = _cap(level, ConfidenceLevel.LIMITED)
        basis.add("section_support_partial")

    if coverage.status is CoverageStatus.UNAVAILABLE:
        level = _cap(level, ConfidenceLevel.UNAVAILABLE)
        basis.add("partial_section_denominators")
    elif coverage.status is CoverageStatus.INSUFFICIENT_EVIDENCE:
        level = _cap(level, ConfidenceLevel.LIMITED)
        basis.add("mixed_assessment_coverage")
    elif coverage.status is CoverageStatus.PARTIAL:
        level = _cap(level, ConfidenceLevel.MODERATE)
        basis.add("mixed_assessment_coverage")
    else:
        basis.add("complete_section_denominators")

    if weakest is ConfidenceLevel.UNAVAILABLE and included > 0:
        level = _cap(level, ConfidenceLevel.UNAVAILABLE)
        basis.add("mixed_source_confidence")
    elif weakest is ConfidenceLevel.LIMITED:
        level = _cap(level, ConfidenceLevel.LIMITED)
        basis.add("mixed_source_confidence")
    elif weakest is ConfidenceLevel.MODERATE:
        level = _cap(level, ConfidenceLevel.MODERATE)
        basis.add("mixed_source_confidence")

    if comparability.schema_compatibility is ComparabilityStatus.NOT_COMPARABLE:
        level = _cap(level, ConfidenceLevel.LIMITED)
        basis.add("schema_mixed")
    elif comparability.schema_compatibility is ComparabilityStatus.PARTIALLY_COMPARABLE:
        level = _cap(level, ConfidenceLevel.MODERATE)
        basis.add("schema_mixed")
    elif comparability.schema_compatibility is ComparabilityStatus.COMPARABLE:
        basis.add("schema_compatible")

    if comparability.methodology_compatibility is ComparabilityStatus.PARTIALLY_COMPARABLE:
        level = _cap(level, ConfidenceLevel.MODERATE)
        basis.add("methodology_partially_compatible")
    elif comparability.methodology_compatibility is ComparabilityStatus.COMPARABLE:
        basis.add("methodology_compatible")

    if comparability.legacy_repository_count > 0:
        level = _cap(level, ConfidenceLevel.LIMITED)
        basis.add("legacy_source_presence")

    if comparability.missing_revision_repository_ids:
        level = _cap(level, ConfidenceLevel.MODERATE)
        basis.add("missing_source_revisions")
    elif included > 0:
        basis.add("public_source_revisions_pinned")

    if comparability.fixture_repository_ids:
        basis.add("controlled_fixture_presence")

    material_limitations = [
        item for item in limitations if item.severity is LimitationSeverity.MATERIAL
    ]
    if material_limitations:
        # Selection bias / representation material limitations cap High.
        level = _cap(level, ConfidenceLevel.MODERATE)
        if any(
            item.category.value
            in {
                "sample_size",
                "assessment_coverage",
                "assessment_confidence",
                "schema_compatibility",
                "denominator_availability",
            }
            for item in material_limitations
        ):
            if included <= 1 or unavailable_material > 0 or weakest is ConfidenceLevel.UNAVAILABLE:
                level = _cap(level, ConfidenceLevel.UNAVAILABLE if included == 0 else ConfidenceLevel.LIMITED)

    # Non-temporal is mandatory; policy may prevent High.
    if any(item.category.value == "non_temporal_dataset" for item in limitations):
        basis.add("non_temporal_dataset")
        if policy.non_temporal_blocks_high:
            level = _cap(level, ConfidenceLevel.MODERATE)

    # High requires strict conditions.
    if level is ConfidenceLevel.HIGH:
        allows_moderate_weakest = (
            policy.high_allows_weakest_moderate
            and weakest in {ConfidenceLevel.HIGH, ConfidenceLevel.MODERATE}
        )
        strict_ok = (
            comparable >= policy.high_minimum_comparable_repository_count
            and comparability.schema_compatibility is ComparabilityStatus.COMPARABLE
            and coverage.status is CoverageStatus.COMPLETE
            and unavailable_material == 0
            and supported_material >= max(1, material_count - 1)
            and (weakest is ConfidenceLevel.HIGH or allows_moderate_weakest)
            and comparability.legacy_repository_count == 0
            and not comparability.missing_revision_repository_ids
            and (not material_limitations or not policy.high_requires_no_material_limitations)
        )
        # Selection-bias material limitations always block High.
        if any(
            item.category.value == "selection_bias" and item.severity is LimitationSeverity.MATERIAL
            for item in limitations
        ):
            strict_ok = False
        if not strict_ok:
            level = ConfidenceLevel.MODERATE

    limitation_ids = tuple(sorted({item.limitation_id.value for item in limitations}))
    if level in {ConfidenceLevel.LIMITED, ConfidenceLevel.UNAVAILABLE} and not limitation_ids:
        # Fail closed — should not happen when limitations builder runs first.
        limitation_ids = ("limitation:quality-derivation-requires-explicit-limitation",)

    if small_sample_sections > 0:
        basis.add("small_repository_sample")

    return IntelligenceReportConfidence(
        level=level,
        basis=tuple(sorted(basis)),
        repository_sample_count=included,
        comparable_repository_count=comparable,
        assessment_schema_compatibility=comparability.schema_compatibility,
        dataset_coverage_status=coverage.status,
        weakest_material_source_confidence=weakest,
        limitations=limitation_ids,
        derivation_status=DerivationStatus.DERIVED,
    )
