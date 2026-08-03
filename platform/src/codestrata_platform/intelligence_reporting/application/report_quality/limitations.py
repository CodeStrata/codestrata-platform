"""Structured DatasetLimitation generation and section-local promotion."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    CrossRepositoryAggregation,
)
from codestrata_platform.intelligence_reporting.application.report_quality.comparability import (
    ComparabilitySummary,
)
from codestrata_platform.intelligence_reporting.application.report_quality.coverage import (
    DatasetCoverageSummary,
)
from codestrata_platform.intelligence_reporting.application.report_quality.policy import (
    ReportQualityPolicy,
    SourceDiversityMode,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ComparabilityStatus,
    ConfidenceLevel,
    CoverageStatus,
    DataVisibility,
    LimitationCategory,
    LimitationSeverity,
    ReportScope,
)
from codestrata_platform.intelligence_reporting.domain.limitations import DatasetLimitation
from codestrata_platform.intelligence_reporting.domain.report import (
    EngineeringIntelligenceReport,
)


def _limitation(
    *,
    category: LimitationCategory,
    severity: LimitationSeverity,
    subject: str,
    statement: str,
    remediation: str,
    repository_ids: Sequence[str] = (),
    head_ids: Sequence[str] = (),
    observation_ids: Sequence[str] = (),
    customer_visible: bool = True,
) -> DatasetLimitation:
    # Stable subject embedded in statement prefix so template wording changes
    # that keep the same subject+scope produce the same ID under Slice 6.1
    # identity (category + statement + repos).
    bound = f"[{subject}] {statement}"
    return DatasetLimitation.create(
        category=category,
        severity=severity,
        statement=bound,
        affected_repository_ids=repository_ids,
        affected_assessment_head_ids=head_ids,
        affected_observation_ids=observation_ids,
        remediation_or_interpretation=remediation,
        customer_visible=customer_visible,
    )


def build_report_limitations(
    report: EngineeringIntelligenceReport,
    aggregation: CrossRepositoryAggregation,
    *,
    policy: ReportQualityPolicy,
    coverage: DatasetCoverageSummary,
    comparability: ComparabilitySummary,
    weakest_material_confidence: ConfidenceLevel,
) -> tuple[DatasetLimitation, ...]:
    """Build deduplicated report-level DatasetLimitation objects."""

    rows: list[DatasetLimitation] = []
    included = tuple(sorted(report.dataset.included_repository_ids))
    public_ids = {
        ref.repository_id
        for ref in report.dataset.repository_assessments
        if ref.repository_id in included
        and ref.visibility is DataVisibility.PUBLIC
    }
    private_ids = {
        ref.repository_id
        for ref in report.dataset.repository_assessments
        if ref.repository_id in included
        and ref.visibility
        in {DataVisibility.CUSTOMER_PRIVATE, DataVisibility.INTERNAL}
    }
    is_public_scope = report.report_scope is ReportScope.PUBLIC_OSS_DATASET

    # Mandatory non-temporal disclosure.
    rows.append(
        _limitation(
            category=LimitationCategory.NON_TEMPORAL_DATASET,
            severity=LimitationSeverity.INFORMATIONAL
            if not policy.non_temporal_blocks_high
            else LimitationSeverity.MODERATE,
            subject="non_temporal_snapshot",
            statement=(
                "This report is a cross-sectional snapshot of the selected assessed "
                "dataset. It does not establish improvement, decline, progress, or "
                "regression over time."
            ),
            remediation=(
                "Interpret distributions and observations as point-in-time facts for "
                "the selected dataset only."
            ),
            repository_ids=(),
            customer_visible=True,
        )
    )

    # Selection bias for curated/public/validation scopes.
    if report.report_scope in policy.selection_bias_scopes:
        severity = (
            LimitationSeverity.MATERIAL
            if report.report_scope is ReportScope.PUBLIC_OSS_DATASET
            else LimitationSeverity.MODERATE
        )
        rows.append(
            _limitation(
                category=LimitationCategory.SELECTION_BIAS,
                severity=severity,
                subject=f"selection:{report.report_scope.value}",
                statement=(
                    "Repository selection for this dataset was curated or "
                    "validation-driven. The dataset is not a random sample and is not "
                    "representative of all software repositories. Observed "
                    "distributions must not be generalized as industry prevalence."
                ),
                remediation=(
                    "Limit conclusions to the selected dataset; do not treat counts as "
                    "industry benchmarks."
                ),
                customer_visible=True,
            )
        )

    # Sample size.
    if comparability.included_repository_count == 0:
        rows.append(
            _limitation(
                category=LimitationCategory.SAMPLE_SIZE,
                severity=LimitationSeverity.MATERIAL,
                subject="sample:zero",
                statement="No repositories are included in this dataset.",
                remediation="Include comparable canonical assessments before interpreting.",
            )
        )
    elif comparability.included_repository_count == 1:
        rows.append(
            _limitation(
                category=LimitationCategory.SAMPLE_SIZE,
                severity=LimitationSeverity.MATERIAL,
                subject="sample:one",
                statement=(
                    "Only one repository is included; cross-repository intelligence "
                    "is not supported for this sample."
                ),
                remediation="Add additional comparable repositories for portfolio interpretation.",
                repository_ids=included,
            )
        )
    elif comparability.included_repository_count < policy.minimum_repository_count:
        rows.append(
            _limitation(
                category=LimitationCategory.SAMPLE_SIZE,
                severity=LimitationSeverity.MATERIAL,
                subject=f"sample:below_min:{comparability.included_repository_count}",
                statement=(
                    f"Included repository count ({comparability.included_repository_count}) "
                    f"is below the policy minimum ({policy.minimum_repository_count})."
                ),
                remediation="Treat conclusions as provisional for this small sample.",
                repository_ids=included,
            )
        )
    elif comparability.included_repository_count < policy.small_sample_threshold:
        rows.append(
            _limitation(
                category=LimitationCategory.SAMPLE_SIZE,
                severity=LimitationSeverity.MODERATE,
                subject=f"sample:small:{comparability.included_repository_count}",
                statement=(
                    f"The included repository sample ({comparability.included_repository_count}) "
                    "is small under the report-quality policy; broad generalization is constrained."
                ),
                remediation="Qualify all portfolio conclusions with the small-sample boundary.",
                repository_ids=included,
            )
        )

    if (
        comparability.comparable_repository_count
        < policy.minimum_comparable_repository_count
        and comparability.included_repository_count > 0
    ):
        rows.append(
            _limitation(
                category=LimitationCategory.SAMPLE_SIZE,
                severity=LimitationSeverity.MATERIAL,
                subject=f"comparable:small:{comparability.comparable_repository_count}",
                statement=(
                    f"Comparable repository count ({comparability.comparable_repository_count}) "
                    "is below the policy minimum for material cross-repository sections."
                ),
                remediation="Do not treat incomparable repositories as a single comparable cohort.",
            )
        )

    # Coverage.
    if coverage.status is CoverageStatus.UNAVAILABLE:
        rows.append(
            _limitation(
                category=LimitationCategory.ASSESSMENT_COVERAGE,
                severity=LimitationSeverity.MATERIAL,
                subject="coverage:unavailable",
                statement=(
                    "Material assessment-head coverage is unavailable for the selected dataset."
                ),
                remediation="Confirm assessment coverage maps before interpreting head distributions.",
                head_ids=coverage.unavailable_head_ids,
            )
        )
    elif coverage.status is CoverageStatus.INSUFFICIENT_EVIDENCE:
        rows.append(
            _limitation(
                category=LimitationCategory.ASSESSMENT_COVERAGE,
                severity=LimitationSeverity.MATERIAL,
                subject="coverage:insufficient",
                statement=(
                    "Material assessment-head coverage is insufficient for one or more heads."
                ),
                remediation="Interpret head comparisons only where coverage is complete or partial.",
                head_ids=coverage.partial_head_ids + coverage.unavailable_head_ids,
            )
        )
    elif coverage.status is CoverageStatus.PARTIAL:
        rows.append(
            _limitation(
                category=LimitationCategory.ASSESSMENT_COVERAGE,
                severity=LimitationSeverity.MODERATE,
                subject="coverage:partial",
                statement=(
                    "Material assessment-head coverage is partial for one or more heads."
                ),
                remediation="Do not treat partial coverage as complete absence of risk or findings.",
                head_ids=coverage.partial_head_ids,
            )
        )
    if coverage.disabled_head_count > 0:
        rows.append(
            _limitation(
                category=LimitationCategory.ASSESSMENT_COVERAGE,
                severity=LimitationSeverity.INFORMATIONAL,
                subject=f"coverage:disabled:{coverage.disabled_head_count}",
                statement=(
                    f"{coverage.disabled_head_count} assessment head(s) are disabled or "
                    "not applicable and are not treated as assessment failures."
                ),
                remediation="Disabled heads do not imply zero risk; they were not evaluated.",
            )
        )

    # Source confidence.
    if weakest_material_confidence is ConfidenceLevel.UNAVAILABLE:
        rows.append(
            _limitation(
                category=LimitationCategory.ASSESSMENT_CONFIDENCE,
                severity=LimitationSeverity.MATERIAL,
                subject="confidence:unavailable",
                statement=(
                    "Weakest materially contributing assessment-head confidence is unavailable."
                ),
                remediation="Do not promote report confidence above the weakest material source.",
            )
        )
    elif weakest_material_confidence is ConfidenceLevel.LIMITED:
        rows.append(
            _limitation(
                category=LimitationCategory.ASSESSMENT_CONFIDENCE,
                severity=LimitationSeverity.MODERATE,
                subject="confidence:limited",
                statement=(
                    "Weakest materially contributing assessment-head confidence is limited."
                ),
                remediation="Report confidence is capped by weakest-material-support policy.",
            )
        )

    # Schema / methodology / legacy / revisions.
    if comparability.schema_compatibility is ComparabilityStatus.NOT_COMPARABLE:
        rows.append(
            _limitation(
                category=LimitationCategory.SCHEMA_COMPATIBILITY,
                severity=LimitationSeverity.MATERIAL,
                subject="schema:incompatible",
                statement=(
                    "Included assessments are not schema-compatible for material comparison. "
                    f"Observed schema versions: {', '.join(comparability.schema_versions) or 'none'}."
                ),
                remediation="Restrict interpretation to schema-compatible subsets.",
            )
        )
    elif comparability.schema_compatibility is ComparabilityStatus.PARTIALLY_COMPARABLE:
        rows.append(
            _limitation(
                category=LimitationCategory.SCHEMA_COMPATIBILITY,
                severity=LimitationSeverity.MODERATE,
                subject="schema:mixed",
                statement=(
                    "Included assessments use mixed assessment schema versions "
                    f"({', '.join(comparability.schema_versions)})."
                ),
                remediation="Prefer per-head comparable subsets when interpreting distributions.",
            )
        )

    if comparability.methodology_compatibility is ComparabilityStatus.PARTIALLY_COMPARABLE:
        rows.append(
            _limitation(
                category=LimitationCategory.METHODOLOGY_COMPATIBILITY,
                severity=LimitationSeverity.MODERATE,
                subject="methodology:mixed",
                statement=(
                    "Methodology versions differ across included assessments "
                    f"({', '.join(comparability.methodology_versions)})."
                ),
                remediation="Do not assume identical methodology across the full population.",
            )
        )

    if comparability.legacy_repository_count > 0:
        rows.append(
            _limitation(
                category=LimitationCategory.LEGACY_SOURCE,
                severity=LimitationSeverity.MODERATE
                if policy.legacy_policy.value == "include_limited"
                else LimitationSeverity.MATERIAL,
                subject=f"legacy:{comparability.legacy_repository_count}",
                statement=(
                    f"{comparability.legacy_repository_count} included repository assessment(s) "
                    "are legacy-limited and must not be treated as canonical-complete."
                ),
                remediation="Separate legacy-limited sources when drawing portfolio conclusions.",
            )
        )

    if comparability.missing_revision_repository_ids:
        visible_repos = _visibility_filter(
            comparability.missing_revision_repository_ids,
            public_ids=public_ids,
            private_ids=private_ids,
            is_public_scope=is_public_scope,
        )
        rows.append(
            _limitation(
                category=LimitationCategory.MISSING_REVISION,
                severity=LimitationSeverity.MODERATE,
                subject="revision:missing",
                statement=(
                    "One or more public/remote assessments lack pinned source revisions, "
                    "reducing revision-level comparability."
                ),
                remediation="Pin revisions for public OSS assessments when possible.",
                repository_ids=visible_repos.ids,
                customer_visible=visible_repos.customer_visible,
            )
        )

    # Representation / fixtures.
    rows.extend(
        _representation_limitations(
            report,
            policy=policy,
            included=included,
            public_ids=public_ids,
            private_ids=private_ids,
            is_public_scope=is_public_scope,
            fixture_ids=comparability.fixture_repository_ids,
        )
    )

    # Section-local promotion + small-sample pattern/observation.
    rows.extend(_promote_section_limitations(report))
    rows.extend(_small_entity_sample_limitations(report))

    # Technology denominator availability.
    tech_denom = report.technology_distribution.repository_denominator
    if (
        "technology_distribution" in policy.material_sections
        and tech_denom == 0
        and report.technology_distribution.observations
    ):
        rows.append(
            _limitation(
                category=LimitationCategory.DENOMINATOR_AVAILABILITY,
                severity=LimitationSeverity.MATERIAL,
                subject="tech:denominator_unavailable",
                statement=(
                    "Technology Distribution observations are present but the section "
                    "denominator is unavailable."
                ),
                remediation="Do not interpret technology ratios without an explicit denominator.",
            )
        )
    elif (
        "technology_distribution" in policy.material_sections
        and tech_denom == 0
        and not report.technology_distribution.observations
        and comparability.included_repository_count > 0
    ):
        rows.append(
            _limitation(
                category=LimitationCategory.SECTION_SUPPORT,
                severity=LimitationSeverity.MODERATE,
                subject="tech:unsupported",
                statement=(
                    "Technology Distribution has no usable denominator for the selected dataset."
                ),
                remediation="Technology presence conclusions are unavailable for this dataset.",
            )
        )

    # Excluded repositories honesty for customer portfolios.
    if (
        report.report_scope
        in {ReportScope.CUSTOMER_PORTFOLIO, ReportScope.CUSTOMER_WORKSPACE}
        and comparability.excluded_repository_count > 0
    ):
        rows.append(
            _limitation(
                category=LimitationCategory.SELECTION_BIAS,
                severity=LimitationSeverity.MODERATE,
                subject=f"customer_excluded:{comparability.excluded_repository_count}",
                statement=(
                    f"{comparability.excluded_repository_count} repository assessment(s) were "
                    "excluded from the selected portfolio dataset."
                ),
                remediation="Interpret results as the included assessed subset, not the full estate.",
            )
        )

    return dedupe_limitations(rows)


def dedupe_limitations(
    limitations: Iterable[DatasetLimitation],
) -> tuple[DatasetLimitation, ...]:
    """Deduplicate by limitation_id; keep first occurrence in stable category order."""

    seen: set[str] = set()
    ordered = sorted(
        limitations,
        key=lambda item: (
            item.category.value,
            item.severity.value,
            item.limitation_id.value,
        ),
    )
    unique: list[DatasetLimitation] = []
    for item in ordered:
        if item.limitation_id.value in seen:
            continue
        seen.add(item.limitation_id.value)
        unique.append(item)
    return tuple(unique)


def _representation_limitations(
    report: EngineeringIntelligenceReport,
    *,
    policy: ReportQualityPolicy,
    included: Sequence[str],
    public_ids: set[str],
    private_ids: set[str],
    is_public_scope: bool,
    fixture_ids: Sequence[str],
) -> list[DatasetLimitation]:
    rows: list[DatasetLimitation] = []
    mode = policy.diversity_mode_for_scope(report.report_scope)
    tech = report.technology_distribution
    denom = tech.repository_denominator
    language_obs = [
        item for item in tech.observations if item.category.lower() in {"language", "languages"}
    ]
    if denom > 0 and language_obs:
        top = max(language_obs, key=lambda item: item.repository_count)
        # Concentration across top languages if multiple share dominance.
        language_repos: set[str] = set()
        for item in language_obs:
            language_repos.update(item.repository_ids)
        # Dominant language share of denominator.
        share = top.repository_count / denom if denom else 0.0
        if share >= policy.language_concentration_threshold and top.repository_count >= 2:
            severity = (
                LimitationSeverity.MATERIAL
                if mode is SourceDiversityMode.MATERIAL_FOR_PUBLIC
                else LimitationSeverity.INFORMATIONAL
            )
            names = ", ".join(
                sorted(
                    {
                        item.normalized_name
                        for item in language_obs
                        if item.repository_count >= max(1, int(denom * 0.25))
                    }
                )
            )
            rows.append(
                _limitation(
                    category=LimitationCategory.LANGUAGE_REPRESENTATION,
                    severity=severity,
                    subject=f"language:{top.normalized_name.lower()}",
                    statement=(
                        f"{names or top.normalized_name} repositories account for "
                        f"{top.repository_count} of {denom} repositories in this selected "
                        "dataset; findings may not generalize to other language ecosystems."
                    ),
                    remediation=(
                        "Treat language concentration as a property of the selected dataset."
                    ),
                    repository_ids=_visibility_filter(
                        top.repository_ids,
                        public_ids=public_ids,
                        private_ids=private_ids,
                        is_public_scope=is_public_scope,
                    ).ids
                    if not is_public_scope
                    else (),
                )
            )

    ecosystem_obs = [
        item
        for item in tech.observations
        if item.category.lower()
        in {"ecosystem", "package_ecosystem", "dependency_ecosystem", "framework"}
    ]
    if denom > 0 and ecosystem_obs:
        top_eco = max(ecosystem_obs, key=lambda item: item.repository_count)
        share = top_eco.repository_count / denom
        if share >= policy.language_concentration_threshold and top_eco.repository_count >= 2:
            severity = (
                LimitationSeverity.MATERIAL
                if mode is SourceDiversityMode.MATERIAL_FOR_PUBLIC
                else LimitationSeverity.INFORMATIONAL
            )
            rows.append(
                _limitation(
                    category=LimitationCategory.ECOSYSTEM_REPRESENTATION,
                    severity=severity,
                    subject=f"ecosystem:{top_eco.normalized_name.lower()}",
                    statement=(
                        f"{top_eco.normalized_name} accounts for {top_eco.repository_count} of "
                        f"{denom} repositories in this selected dataset; findings may not "
                        "generalize to other ecosystems."
                    ),
                    remediation=(
                        "Treat ecosystem concentration as descriptive of the selected dataset."
                    ),
                )
            )

    included_count = len(included)
    if fixture_ids and included_count > 0:
        fixture_share = len(fixture_ids) / included_count
        if (
            mode is SourceDiversityMode.FIXTURE_EXPLICIT_FOR_VALIDATION
            or fixture_share >= policy.fixture_concentration_threshold
        ):
            severity = (
                LimitationSeverity.MATERIAL
                if mode is SourceDiversityMode.FIXTURE_EXPLICIT_FOR_VALIDATION
                and fixture_share >= policy.fixture_concentration_threshold
                else LimitationSeverity.MODERATE
            )
            rows.append(
                _limitation(
                    category=LimitationCategory.CONTROLLED_FIXTURE_PRESENCE,
                    severity=severity,
                    subject=f"fixtures:{len(fixture_ids)}",
                    statement=(
                        f"{len(fixture_ids)} of {included_count} included repositories are "
                        "controlled fixtures or internal-validation sources; interpretation "
                        "must separate fixture composition from real-world portfolios."
                    ),
                    remediation=(
                        "Disclose fixture presence; do not present fixture-heavy results as "
                        "industry prevalence."
                    ),
                    repository_ids=() if is_public_scope else tuple(sorted(fixture_ids)),
                    customer_visible=True,
                )
            )

    # Source-type concentration (factual).
    by_type: dict[str, int] = {}
    for ref in report.dataset.repository_assessments:
        if ref.repository_id not in included:
            continue
        by_type[ref.source_type.value] = by_type.get(ref.source_type.value, 0) + 1
    if included_count > 0 and by_type:
        dominant_type, dominant_count = max(by_type.items(), key=lambda item: item[1])
        if dominant_count / included_count >= 0.9 and included_count >= 2:
            severity = (
                LimitationSeverity.MODERATE
                if mode is SourceDiversityMode.MATERIAL_FOR_PUBLIC
                else LimitationSeverity.INFORMATIONAL
            )
            rows.append(
                _limitation(
                    category=LimitationCategory.SOURCE_VISIBILITY,
                    severity=severity,
                    subject=f"source_type:{dominant_type}",
                    statement=(
                        f"Source type '{dominant_type}' accounts for {dominant_count} of "
                        f"{included_count} included repositories in this selected dataset."
                    ),
                    remediation="Interpret source-type concentration as a dataset property.",
                )
            )

    return rows


_MATERIAL_LOCAL_TOKENS = (
    "unavailable",
    "denominator",
    "partial",
    "legacy",
    "incomplete_support",
    "missing_coverage",
    "not_comparable",
)


def _is_material_local_code(code: str) -> bool:
    lowered = code.lower()
    return any(token in lowered for token in _MATERIAL_LOCAL_TOKENS)


def _promote_section_limitations(
    report: EngineeringIntelligenceReport,
) -> list[DatasetLimitation]:
    """Promote material section-local codes; preserve others on their sections."""

    rows: list[DatasetLimitation] = []

    tech_codes = tuple(report.technology_distribution.limitations)
    if tech_codes:
        material_codes = tuple(code for code in tech_codes if _is_material_local_code(code))
        if material_codes:
            preview = ", ".join(material_codes[:8])
            rows.append(
                _limitation(
                    category=LimitationCategory.SECTION_SUPPORT,
                    severity=LimitationSeverity.MODERATE,
                    subject=f"tech_local:{len(material_codes)}",
                    statement=(
                        f"Technology Distribution includes {len(material_codes)} material local "
                        f"limitation disclosure(s) ({preview}). "
                        "Section-local detail remains authoritative."
                    ),
                    remediation="Interpret technology counts with the listed section limitations.",
                )
            )
        else:
            rows.append(
                _limitation(
                    category=LimitationCategory.SECTION_SUPPORT,
                    severity=LimitationSeverity.INFORMATIONAL,
                    subject=f"tech_local_present:{len(tech_codes)}",
                    statement=(
                        f"Technology Distribution retains {len(tech_codes)} section-local "
                        "limitation disclosure(s)."
                    ),
                    remediation="Consult Technology Distribution.limitations for section detail.",
                )
            )

    capability_heads: set[str] = set()
    capability_code_count = 0
    for comparison in report.capability_comparisons:
        for code in comparison.limitations:
            if _is_material_local_code(code):
                capability_heads.add(comparison.assessment_head_id)
                capability_code_count += 1
    if capability_code_count:
        head_list = ", ".join(sorted(capability_heads)[:12])
        rows.append(
            _limitation(
                category=LimitationCategory.SECTION_SUPPORT,
                severity=LimitationSeverity.MODERATE,
                subject=f"capability_local:{capability_code_count}:{len(capability_heads)}",
                statement=(
                    f"Capability Comparison includes {capability_code_count} material local "
                    f"limitation disclosure(s) across heads: {head_list}. "
                    "Head-local detail remains authoritative."
                ),
                remediation="Preserve head-local limitations when reading distributions.",
                head_ids=tuple(sorted(capability_heads)),
            )
        )

    pattern_material = [
        f"{pattern.pattern_id.value}:{code}"
        for pattern in report.recurring_patterns
        for code in pattern.limitations
        if _is_material_local_code(code)
    ]
    if pattern_material:
        rows.append(
            _limitation(
                category=LimitationCategory.SECTION_SUPPORT,
                severity=LimitationSeverity.INFORMATIONAL,
                subject=f"pattern_local:{len(pattern_material)}",
                statement=(
                    "Recurring patterns include material local limitation disclosures; "
                    "pattern-local limitations remain authoritative."
                ),
                remediation="Consult each pattern.limitations entry for support constraints.",
            )
        )

    observation_material = [
        f"{observation.observation_id.value}:{code}"
        for observation in report.modernization_observations
        for code in observation.limitations
        if _is_material_local_code(code)
    ]
    if observation_material:
        rows.append(
            _limitation(
                category=LimitationCategory.SECTION_SUPPORT,
                severity=LimitationSeverity.INFORMATIONAL,
                subject=f"observation_local:{len(observation_material)}",
                statement=(
                    "Modernization observations include material support-chain limitation "
                    "disclosures; observation-local limitations remain authoritative."
                ),
                remediation="Consult each observation.limitations entry for support constraints.",
            )
        )
    return rows


def _small_entity_sample_limitations(
    report: EngineeringIntelligenceReport,
) -> list[DatasetLimitation]:
    rows: list[DatasetLimitation] = []
    for pattern in report.recurring_patterns:
        if len(pattern.repository_ids) == 2:
            rows.append(
                _limitation(
                    category=LimitationCategory.SAMPLE_SIZE,
                    severity=LimitationSeverity.MINOR,
                    subject=f"pattern_sample:{pattern.pattern_id.value}",
                    statement=(
                        f"Recurring pattern '{pattern.pattern_id.value}' is supported by "
                        "exactly two repositories; interpret as a minimal recurring signal."
                    ),
                    remediation="Do not treat two-repository patterns as broad prevalence.",
                    repository_ids=pattern.repository_ids,
                )
            )
    for observation in report.modernization_observations:
        if len(observation.repository_ids) == 2:
            rows.append(
                _limitation(
                    category=LimitationCategory.SAMPLE_SIZE,
                    severity=LimitationSeverity.MINOR,
                    subject=f"observation_sample:{observation.observation_id.value}",
                    statement=(
                        f"Modernization observation '{observation.observation_id.value}' is "
                        "supported by exactly two repositories."
                    ),
                    remediation="Qualify two-repository observations as minimal portfolio signals.",
                    observation_ids=(observation.observation_id.value,),
                    repository_ids=observation.repository_ids,
                )
            )
    for head in report.assessment_head_distributions:
        if 0 < head.repository_count < 3:
            rows.append(
                _limitation(
                    category=LimitationCategory.SAMPLE_SIZE,
                    severity=LimitationSeverity.MINOR,
                    subject=f"head_denom:{head.assessment_head_id}:{head.repository_count}",
                    statement=(
                        f"Assessment-head '{head.assessment_head_id}' distribution is based on "
                        f"{head.repository_count} repositories; broad interpretation is constrained."
                    ),
                    remediation="Prefer larger denominators before generalizing head distributions.",
                    head_ids=(head.assessment_head_id,),
                )
            )
    return rows


class _VisibleRepos:
    def __init__(self, ids: Sequence[str], customer_visible: bool) -> None:
        self.ids = tuple(ids)
        self.customer_visible = customer_visible


def _visibility_filter(
    repository_ids: Sequence[str],
    *,
    public_ids: set[str],
    private_ids: set[str],
    is_public_scope: bool,
) -> _VisibleRepos:
    ids = tuple(sorted({item for item in repository_ids if item}))
    if not is_public_scope:
        return _VisibleRepos(ids, True)
    # Public-scope limitations must not leak private repository IDs.
    if any(item in private_ids for item in ids):
        public_only = tuple(sorted(item for item in ids if item in public_ids))
        return _VisibleRepos(public_only, True)
    return _VisibleRepos(ids, True)
