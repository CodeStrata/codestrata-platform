"""Deterministic comparison helpers for validation expectations."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from validation.models import (
    ActualAssessmentResult,
    ComparisonMismatch,
    ComparisonOutcome,
    CountRange,
    ExpectedResults,
    PackPrecisionRecord,
)
from validation.inventory import (
    FactClassification,
    InventoryValidationResult,
    validate_technology_inventory,
)
from validation.security import (
    SecurityValidationResult,
    validate_security_precision,
)
from validation.architecture import (
    ArchitectureValidationResult,
    validate_architecture_precision,
)
from validation.technical_debt import (
    TechnicalDebtValidationResult,
    validate_technical_debt_precision,
)
from validation.dependency import (
    DependencyValidationResult,
    validate_dependency_precision,
)
from validation.cloud import (
    CloudValidationResult,
    validate_cloud_precision,
)
from validation.ai_readiness import (
    AiReadinessValidationResult,
    validate_ai_readiness_precision,
)
from validation.modernization import (
    ModernizationValidationResult,
    validate_modernization_precision,
)


def pack_precision_from_result(pack: str, result: object) -> PackPrecisionRecord:
    """Build a pack precision snapshot from a pack ``*ValidationResult``."""

    return PackPrecisionRecord(
        pack=pack,
        true_positives=int(getattr(result, "true_positives", 0) or 0),
        false_positives=int(getattr(result, "false_positives", 0) or 0),
        false_negatives=int(getattr(result, "false_negatives", 0) or 0),
        ambiguous=int(getattr(result, "ambiguous", 0) or 0),
        precision=getattr(result, "precision", None),
        recall=getattr(result, "recall", None),
        passed=getattr(result, "passed", None),
    )


def normalize_repo_relative_path(path: str) -> str:
    """Normalize a path to a stable repository-relative POSIX form."""

    cleaned = path.replace("\\", "/").strip()
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    pure = PurePosixPath(cleaned)
    parts = [part for part in pure.parts if part not in ("", ".")]
    if any(part == ".." for part in parts):
        # Keep as-is after collapsing redundant separators only.
        return str(PurePosixPath(*parts)) if parts else ""
    return str(PurePosixPath(*parts)) if parts else ""


def exact_set_match(expected: set[str], actual: set[str]) -> bool:
    return expected == actual


def required_subset(required: set[str], actual: set[str]) -> set[str]:
    """Return missing members (empty when the required subset is present)."""

    return required - actual


def forbidden_present(forbidden: set[str], actual: set[str]) -> set[str]:
    """Return forbidden members that appear in actual."""

    return forbidden & actual


def count_in_range(value: int, range_: CountRange) -> bool:
    return range_.contains(value)


def compare_actual_to_expected(
    *,
    repository_id: str,
    expected: ExpectedResults,
    actual: ActualAssessmentResult,
    artifact_path: str | None = None,
) -> ComparisonOutcome:
    """Compare normalized actual results to expectations.

    Returns a ``ComparisonOutcome`` with mismatches, expectation counts, and
    pack precision/recall snapshots for permanent recording (Slice 4.11).
    """

    mismatches: list[ComparisonMismatch] = []
    evaluated = 0
    matched = 0
    pack_precision: list[PackPrecisionRecord] = []
    report_path = artifact_path or actual.artifact_paths.get("report.json")

    def _fail(area: str, expectation: str, got: str, diagnostic: str) -> None:
        mismatches.append(
            ComparisonMismatch(
                repository_id=repository_id,
                assessment_area=area,
                expectation=expectation,
                actual=got,
                artifact_path=report_path,
                diagnostic=diagnostic,
            )
        )

    def _check_subset(area: str, required: tuple[str, ...], actual_values: tuple[str, ...]) -> None:
        nonlocal evaluated, matched
        if not required:
            return
        evaluated += 1
        missing = sorted(required_subset(set(required), set(actual_values)))
        if missing:
            _fail(
                area,
                f"required subset {sorted(required)}",
                f"actual={sorted(actual_values)}",
                f"missing {missing}",
            )
        else:
            matched += 1

    def _check_forbidden(
        area: str, forbidden: tuple[str, ...], actual_values: tuple[str, ...]
    ) -> None:
        nonlocal evaluated, matched
        if not forbidden:
            return
        evaluated += 1
        present = sorted(forbidden_present(set(forbidden), set(actual_values)))
        if present:
            _fail(
                area,
                f"forbidden set {sorted(forbidden)}",
                f"actual={sorted(actual_values)}",
                f"forbidden values present: {present}",
            )
        else:
            matched += 1

    def _check_count(area: str, range_: CountRange | None, value: int) -> None:
        nonlocal evaluated, matched
        if range_ is None:
            return
        evaluated += 1
        if count_in_range(value, range_):
            matched += 1
        else:
            _fail(
                area,
                f"count {range_.describe()}",
                f"actual_count={value}",
                f"{area} count {value} outside {range_.describe()}",
            )

    def _check_exact(area: str, expected_value: str | None, actual_value: str | None) -> None:
        nonlocal evaluated, matched
        if expected_value is None:
            return
        evaluated += 1
        if actual_value == expected_value:
            matched += 1
        else:
            _fail(
                area,
                f"exact={expected_value!r}",
                f"actual={actual_value!r}",
                f"{area} mismatch",
            )

    _check_exact("schema_version", expected.schema_version, actual.schema_version)
    _check_exact(
        "assessment_status",
        expected.expected_assessment_status,
        actual.assessment_status,
    )

    _check_subset(
        "technology_inventory",
        expected.technology_facts_expected,
        actual.technologies,
    )
    _check_forbidden(
        "technology_inventory",
        expected.technology_facts_forbidden,
        actual.technologies,
    )

    _check_subset(
        "findings",
        expected.expected_finding_rule_ids,
        actual.finding_rule_ids,
    )
    _check_forbidden(
        "findings",
        expected.forbidden_finding_rule_ids,
        actual.finding_rule_ids,
    )
    _check_count("findings", expected.finding_count, actual.findings_count)

    if expected.minimum_required_detections is not None:
        evaluated += 1
        if actual.findings_count >= expected.minimum_required_detections:
            matched += 1
        else:
            _fail(
                "findings",
                f"minimum_required_detections={expected.minimum_required_detections}",
                f"actual_count={actual.findings_count}",
                "too few detections",
            )

    if expected.maximum_allowed_false_positives is not None:
        # False-positive accounting is pack-specific; this harness records the
        # expectation slot and treats excess forbidden rule hits as FP signal.
        evaluated += 1
        forbidden_hits = len(
            forbidden_present(
                set(expected.forbidden_finding_rule_ids),
                set(actual.finding_rule_ids),
            )
        )
        if forbidden_hits <= expected.maximum_allowed_false_positives:
            matched += 1
        else:
            _fail(
                "findings",
                f"maximum_allowed_false_positives={expected.maximum_allowed_false_positives}",
                f"forbidden_rule_hits={forbidden_hits}",
                "false-positive budget exceeded",
            )

    _check_subset(
        "recommendations",
        expected.expected_recommendation_ids,
        actual.recommendation_ids,
    )
    _check_forbidden(
        "recommendations",
        expected.forbidden_recommendation_ids,
        actual.recommendation_ids,
    )
    _check_subset(
        "recommendations",
        expected.expected_recommendation_categories,
        actual.recommendation_categories,
    )
    _check_count("recommendations", expected.recommendation_count, actual.recommendations_count)

    _check_subset(
        "priority_actions",
        expected.expected_priority_action_categories,
        actual.priority_action_categories,
    )
    _check_subset(
        "roadmap",
        expected.expected_roadmap_phases,
        actual.roadmap_phases,
    )
    _check_subset(
        "coverage",
        expected.expected_coverage_states,
        actual.coverage_states,
    )
    _check_subset(
        "limitations",
        expected.expected_limitations,
        actual.limitations,
    )
    _check_forbidden(
        "limitations",
        expected.forbidden_limitations,
        actual.limitations,
    )

    expected_paths = tuple(normalize_repo_relative_path(p) for p in expected.expected_evidence_paths)
    actual_paths = tuple(normalize_repo_relative_path(p) for p in actual.evidence_paths)
    forbidden_paths = tuple(
        normalize_repo_relative_path(p) for p in expected.forbidden_evidence_paths
    )
    _check_subset("evidence", expected_paths, actual_paths)
    _check_forbidden("evidence", forbidden_paths, actual_paths)

    _check_subset(
        "assessment_heads",
        expected.expected_assessment_heads,
        actual.assessment_heads,
    )

    if expected.expected_artifacts:
        evaluated += 1
        present = set(actual.artifact_paths)
        missing = sorted(set(expected.expected_artifacts) - present)
        if missing:
            _fail(
                "artifacts",
                f"required artifacts {sorted(expected.expected_artifacts)}",
                f"actual={sorted(present)}",
                f"missing artifacts: {missing}",
            )
        else:
            matched += 1

    if expected.expect_ai_executed is not None:
        evaluated += 1
        if actual.ai_executed is expected.expect_ai_executed:
            matched += 1
        else:
            _fail(
                "ai",
                f"expect_ai_executed={expected.expect_ai_executed}",
                f"actual_ai_executed={actual.ai_executed}",
                "AI execution expectation mismatch",
            )

    if expected.technology_inventory is not None:
        inventory_actual = dict(actual.technologies_by_category)
        inventory_actual["dependency_ecosystems"] = actual.dependency_ecosystems
        inventory_actual["composition"] = actual.repository_composition_facts
        inventory_actual["application_indicators"] = actual.application_indicators
        inventory_result = validate_technology_inventory(
            repository_id=repository_id,
            expectation=expected.technology_inventory,
            actual_by_category=inventory_actual,
            actual_versions=actual.technology_versions,
        )
        pack_precision.append(
            pack_precision_from_result("technology_inventory", inventory_result)
        )
        inv_mismatches, inv_evaluated, inv_matched = _inventory_to_mismatches(
            inventory_result,
            artifact_path=report_path,
        )
        mismatches.extend(inv_mismatches)
        evaluated += inv_evaluated
        matched += inv_matched

    if expected.security is not None:
        artifact_texts = _load_artifact_texts(actual.artifact_paths)
        security_result = validate_security_precision(
            repository_id=repository_id,
            expectation=expected.security,
            actual_findings=actual.security_findings,
            artifact_texts=artifact_texts,
        )
        pack_precision.append(pack_precision_from_result("security", security_result))
        sec_mismatches, sec_evaluated, sec_matched = _security_to_mismatches(
            security_result,
            artifact_path=report_path,
        )
        mismatches.extend(sec_mismatches)
        evaluated += sec_evaluated
        matched += sec_matched

    if expected.architecture is not None:
        artifact_texts = _load_artifact_texts(actual.artifact_paths)
        architecture_result = validate_architecture_precision(
            repository_id=repository_id,
            expectation=expected.architecture,
            actual_findings=actual.architecture_findings,
            graph=actual.architecture_graph,
            artifact_texts=artifact_texts,
        )
        pack_precision.append(
            pack_precision_from_result("architecture", architecture_result)
        )
        arch_mismatches, arch_evaluated, arch_matched = _architecture_to_mismatches(
            architecture_result,
            artifact_path=report_path,
        )
        mismatches.extend(arch_mismatches)
        evaluated += arch_evaluated
        matched += arch_matched

    if expected.technical_debt is not None:
        artifact_texts = _load_artifact_texts(actual.artifact_paths)
        td_result = validate_technical_debt_precision(
            repository_id=repository_id,
            expectation=expected.technical_debt,
            actual_findings=actual.technical_debt_findings,
            artifact_texts=artifact_texts,
        )
        pack_precision.append(pack_precision_from_result("technical_debt", td_result))
        td_mismatches, td_evaluated, td_matched = _technical_debt_to_mismatches(
            td_result,
            artifact_path=report_path,
        )
        mismatches.extend(td_mismatches)
        evaluated += td_evaluated
        matched += td_matched

    if expected.dependency is not None:
        artifact_texts = _load_artifact_texts(actual.artifact_paths)
        dep_result = validate_dependency_precision(
            repository_id=repository_id,
            expectation=expected.dependency,
            actual_findings=actual.dependency_findings,
            actual_manifests=actual.dependency_manifests,
            artifact_texts=artifact_texts,
            limitation_texts=actual.limitations,
        )
        pack_precision.append(pack_precision_from_result("dependency", dep_result))
        dep_mismatches, dep_evaluated, dep_matched = _dependency_to_mismatches(
            dep_result,
            artifact_path=report_path,
        )
        mismatches.extend(dep_mismatches)
        evaluated += dep_evaluated
        matched += dep_matched

    if expected.cloud is not None:
        artifact_texts = _load_artifact_texts(actual.artifact_paths)
        cloud_result = validate_cloud_precision(
            repository_id=repository_id,
            expectation=expected.cloud,
            actual_findings=actual.cloud_findings,
            actual_signals=actual.cloud_signals,
            actual_recommendations=actual.cloud_recommendations,
            artifact_texts=artifact_texts,
            limitation_texts=actual.limitations,
        )
        pack_precision.append(pack_precision_from_result("cloud", cloud_result))
        cloud_mismatches, cloud_evaluated, cloud_matched = _cloud_to_mismatches(
            cloud_result,
            artifact_path=report_path,
        )
        mismatches.extend(cloud_mismatches)
        evaluated += cloud_evaluated
        matched += cloud_matched

    if expected.ai_readiness is not None:
        artifact_texts = _load_artifact_texts(actual.artifact_paths)
        ai_result = validate_ai_readiness_precision(
            repository_id=repository_id,
            expectation=expected.ai_readiness,
            actual_findings=actual.ai_readiness_findings,
            actual_signals=actual.ai_readiness_signals,
            actual_recommendations=actual.ai_readiness_recommendations,
            artifact_texts=artifact_texts,
            limitation_texts=actual.limitations,
        )
        pack_precision.append(pack_precision_from_result("ai_readiness", ai_result))
        ai_mismatches, ai_evaluated, ai_matched = _ai_readiness_to_mismatches(
            ai_result,
            artifact_path=report_path,
        )
        mismatches.extend(ai_mismatches)
        evaluated += ai_evaluated
        matched += ai_matched

    if expected.modernization is not None:
        artifact_texts = _load_artifact_texts(actual.artifact_paths)
        modernization_result = validate_modernization_precision(
            repository_id=repository_id,
            expectation=expected.modernization,
            actual_recommendations=actual.modernization_recommendations,
            actual_priority_actions=actual.modernization_priority_actions,
            actual_roadmap_initiatives=actual.modernization_roadmap_initiatives,
            finding_ids=set(actual.finding_ids),
            artifact_texts=artifact_texts,
            limitation_texts=actual.limitations,
            ai_executed=bool(actual.ai_executed),
        )
        pack_precision.append(
            pack_precision_from_result("modernization", modernization_result)
        )
        mod_mismatches, mod_evaluated, mod_matched = _modernization_to_mismatches(
            modernization_result,
            artifact_path=report_path,
        )
        mismatches.extend(mod_mismatches)
        evaluated += mod_evaluated
        matched += mod_matched

    return ComparisonOutcome(
        mismatches=tuple(mismatches),
        expectations_evaluated=evaluated,
        expectations_matched=matched,
        pack_precision=tuple(pack_precision),
    )


def _inventory_to_mismatches(
    result: InventoryValidationResult,
    *,
    artifact_path: str | None,
) -> tuple[list[ComparisonMismatch], int, int]:
    mismatches: list[ComparisonMismatch] = []
    evaluated = 0
    matched = 0
    for item in result.classifications:
        if item.classification is FactClassification.NOT_APPLICABLE:
            continue
        if item.classification is FactClassification.AMBIGUOUS:
            # Explicitly excluded from scoring; still counted as evaluated matched.
            evaluated += 1
            matched += 1
            continue
        if item.classification is FactClassification.TRUE_POSITIVE:
            evaluated += 1
            matched += 1
            continue
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area=f"technology_inventory:{item.category}",
                expectation=item.expectation,
                actual=item.actual,
                artifact_path=artifact_path,
                diagnostic=item.diagnostic,
            )
        )
    return mismatches, evaluated, matched


def _security_to_mismatches(
    result: SecurityValidationResult,
    *,
    artifact_path: str | None,
) -> tuple[list[ComparisonMismatch], int, int]:
    mismatches: list[ComparisonMismatch] = []
    evaluated = 0
    matched = 0
    for item in result.classifications:
        if item.classification is FactClassification.NOT_APPLICABLE:
            continue
        if item.classification is FactClassification.AMBIGUOUS:
            evaluated += 1
            matched += 1
            continue
        if item.classification is FactClassification.TRUE_POSITIVE:
            evaluated += 1
            matched += 1
            continue
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area=f"security:{item.rule_id}",
                expectation=item.expectation,
                actual=item.actual,
                artifact_path=artifact_path,
                diagnostic=item.diagnostic,
            )
        )
    for failure in result.redaction_failures:
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area="security:redaction",
                expectation="forbidden_raw_values absent",
                actual=failure,
                artifact_path=artifact_path,
                diagnostic=failure,
            )
        )
    for failure in result.production_context_errors:
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area="security:context",
                expectation="non-production paths must not be production context",
                actual=failure,
                artifact_path=artifact_path,
                diagnostic=failure,
            )
        )
    return mismatches, evaluated, matched


def _architecture_to_mismatches(
    result: ArchitectureValidationResult,
    *,
    artifact_path: str | None,
) -> tuple[list[ComparisonMismatch], int, int]:
    mismatches: list[ComparisonMismatch] = []
    evaluated = 0
    matched = 0
    for item in result.classifications:
        if item.classification is FactClassification.NOT_APPLICABLE:
            continue
        if item.classification is FactClassification.AMBIGUOUS:
            evaluated += 1
            matched += 1
            continue
        if item.classification is FactClassification.TRUE_POSITIVE:
            evaluated += 1
            matched += 1
            continue
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area=f"architecture:{item.rule_id}",
                expectation=item.expectation,
                actual=item.actual,
                artifact_path=artifact_path,
                diagnostic=item.diagnostic,
            )
        )
    for failure in result.unsupported_claim_failures:
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area="architecture:unsupported_claim",
                expectation="no unsupported runtime architecture claims",
                actual=failure,
                artifact_path=artifact_path,
                diagnostic=failure,
            )
        )
    for failure in result.path_failures:
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area="architecture:traceability",
                expectation="repository-relative evidence-linked architecture finding",
                actual=failure,
                artifact_path=artifact_path,
                diagnostic=failure,
            )
        )
    return mismatches, evaluated, matched


def _technical_debt_to_mismatches(
    result: TechnicalDebtValidationResult,
    *,
    artifact_path: str | None,
) -> tuple[list[ComparisonMismatch], int, int]:
    mismatches: list[ComparisonMismatch] = []
    evaluated = 0
    matched = 0
    for item in result.classifications:
        if item.classification is FactClassification.NOT_APPLICABLE:
            continue
        if item.classification is FactClassification.AMBIGUOUS:
            evaluated += 1
            matched += 1
            continue
        if item.classification is FactClassification.TRUE_POSITIVE:
            evaluated += 1
            matched += 1
            continue
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area=f"technical_debt:{item.rule_id}",
                expectation=item.expectation,
                actual=item.actual,
                artifact_path=artifact_path,
                diagnostic=item.diagnostic,
            )
        )
    for failure in result.unsupported_claim_failures:
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area="technical_debt:unsupported_claim",
                expectation="no unsupported technical debt conclusions",
                actual=failure,
                artifact_path=artifact_path,
                diagnostic=failure,
            )
        )
    for failure in result.measurement_failures:
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area="technical_debt:measurement",
                expectation="exact measurement and threshold preserved",
                actual=failure,
                artifact_path=artifact_path,
                diagnostic=failure,
            )
        )
    for failure in result.context_failures:
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area="technical_debt:context",
                expectation="non-production complexity must not inflate production debt",
                actual=failure,
                artifact_path=artifact_path,
                diagnostic=failure,
            )
        )
    return mismatches, evaluated, matched


def _cloud_to_mismatches(
    result: CloudValidationResult,
    *,
    artifact_path: str | None,
) -> tuple[list[ComparisonMismatch], int, int]:
    mismatches: list[ComparisonMismatch] = []
    evaluated = 0
    matched = 0
    for item in result.classifications:
        if item.classification is FactClassification.NOT_APPLICABLE:
            continue
        if item.classification is FactClassification.AMBIGUOUS:
            evaluated += 1
            matched += 1
            continue
        if item.classification is FactClassification.TRUE_POSITIVE:
            evaluated += 1
            matched += 1
            continue
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area=f"cloud:{item.rule_id}",
                expectation=item.expectation,
                actual=item.actual,
                artifact_path=artifact_path,
                diagnostic=item.diagnostic,
            )
        )
    for failure in result.unsupported_claim_failures:
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area="cloud:unsupported_claim",
                expectation="no unsupported cloud readiness conclusions",
                actual=failure,
                artifact_path=artifact_path,
                diagnostic=failure,
            )
        )
    for failure in result.path_failures:
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area="cloud:traceability",
                expectation="repository-relative evidence-linked cloud finding",
                actual=failure,
                artifact_path=artifact_path,
                diagnostic=failure,
            )
        )
    for failure in result.parse_coverage_failures:
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area="cloud:coverage",
                expectation="honest cloud coverage / limitations",
                actual=failure,
                artifact_path=artifact_path,
                diagnostic=failure,
            )
        )
    return mismatches, evaluated, matched


def _ai_readiness_to_mismatches(
    result: AiReadinessValidationResult,
    *,
    artifact_path: str | None,
) -> tuple[list[ComparisonMismatch], int, int]:
    mismatches: list[ComparisonMismatch] = []
    evaluated = 0
    matched = 0
    for item in result.classifications:
        if item.classification is FactClassification.NOT_APPLICABLE:
            continue
        if item.classification is FactClassification.AMBIGUOUS:
            evaluated += 1
            matched += 1
            continue
        if item.classification is FactClassification.TRUE_POSITIVE:
            evaluated += 1
            matched += 1
            continue
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area=f"ai_readiness:{item.rule_id}",
                expectation=item.expectation,
                actual=item.actual,
                artifact_path=artifact_path,
                diagnostic=item.diagnostic,
            )
        )
    for failure in result.unsupported_claim_failures:
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area="ai_readiness:unsupported_claim",
                expectation="no unsupported AI readiness conclusions",
                actual=failure,
                artifact_path=artifact_path,
                diagnostic=failure,
            )
        )
    for failure in result.path_failures:
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area="ai_readiness:traceability",
                expectation="repository-relative evidence-linked AI Readiness finding",
                actual=failure,
                artifact_path=artifact_path,
                diagnostic=failure,
            )
        )
    for failure in result.parse_coverage_failures:
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area="ai_readiness:coverage",
                expectation="honest AI Readiness coverage / limitations",
                actual=failure,
                artifact_path=artifact_path,
                diagnostic=failure,
            )
        )
    return mismatches, evaluated, matched


def _modernization_to_mismatches(
    result: ModernizationValidationResult,
    *,
    artifact_path: str | None,
) -> tuple[list[ComparisonMismatch], int, int]:
    mismatches: list[ComparisonMismatch] = []
    evaluated = 0
    matched = 0
    for item in result.classifications:
        if item.classification is FactClassification.NOT_APPLICABLE:
            continue
        if item.classification is FactClassification.AMBIGUOUS:
            evaluated += 1
            matched += 1
            continue
        if item.classification is FactClassification.TRUE_POSITIVE:
            evaluated += 1
            matched += 1
            continue
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area=f"modernization:{item.rule_id}",
                expectation=item.expectation,
                actual=item.actual,
                artifact_path=artifact_path,
                diagnostic=item.diagnostic,
            )
        )
    for failure in result.unsupported_claim_failures:
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area="modernization:unsupported_claim",
                expectation="no unsupported modernization conclusions",
                actual=failure,
                artifact_path=artifact_path,
                diagnostic=failure,
            )
        )
    for failure in getattr(result, "path_failures", ()) or ():
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area="modernization:traceability",
                expectation="finding-backed recommendation → PA → roadmap chain",
                actual=failure,
                artifact_path=artifact_path,
                diagnostic=failure,
            )
        )
    for failure in getattr(result, "parse_coverage_failures", ()) or ():
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area="modernization:coverage",
                expectation="honest modernization coverage / limitations",
                actual=failure,
                artifact_path=artifact_path,
                diagnostic=failure,
            )
        )
    return mismatches, evaluated, matched


def _dependency_to_mismatches(
    result: DependencyValidationResult,
    *,
    artifact_path: str | None,
) -> tuple[list[ComparisonMismatch], int, int]:
    mismatches: list[ComparisonMismatch] = []
    evaluated = 0
    matched = 0
    for item in result.classifications:
        if item.classification is FactClassification.NOT_APPLICABLE:
            continue
        if item.classification is FactClassification.AMBIGUOUS:
            evaluated += 1
            matched += 1
            continue
        if item.classification is FactClassification.TRUE_POSITIVE:
            evaluated += 1
            matched += 1
            continue
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area=f"dependency:{item.rule_id}",
                expectation=item.expectation,
                actual=item.actual,
                artifact_path=artifact_path,
                diagnostic=item.diagnostic,
            )
        )
    for failure in result.unsupported_claim_failures:
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area="dependency:unsupported_claim",
                expectation="no unsupported dependency conclusions",
                actual=failure,
                artifact_path=artifact_path,
                diagnostic=failure,
            )
        )
    for failure in result.path_failures:
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area="dependency:traceability",
                expectation="repository-relative evidence-linked dependency finding",
                actual=failure,
                artifact_path=artifact_path,
                diagnostic=failure,
            )
        )
    for failure in result.parse_coverage_failures:
        evaluated += 1
        mismatches.append(
            ComparisonMismatch(
                repository_id=result.repository_id,
                assessment_area="dependency:parse_coverage",
                expectation="honest parse / limitation coverage",
                actual=failure,
                artifact_path=artifact_path,
                diagnostic=failure,
            )
        )
    return mismatches, evaluated, matched


def _load_artifact_texts(artifact_paths: dict[str, str]) -> dict[str, str]:
    texts: dict[str, str] = {}
    for name, path_str in artifact_paths.items():
        if not path_str:
            continue
        path = Path(path_str)
        if not path.is_file():
            continue
        try:
            texts[name] = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    return texts


def ordered_equal(left: list[str] | tuple[str, ...], right: list[str] | tuple[str, ...]) -> bool:
    """Ordered comparison where sequence is meaningful."""

    return tuple(left) == tuple(right)


def safe_artifact_path(path: Path | str, *, base: Path | None = None) -> str:
    """Return a repository-relative path string for summaries (never home paths)."""

    candidate = Path(path)
    if base is not None:
        try:
            return normalize_repo_relative_path(str(candidate.resolve().relative_to(base.resolve())))
        except ValueError:
            pass
    # Fall back to basename-only to avoid leaking absolute user paths.
    return candidate.name

