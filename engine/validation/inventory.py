"""Technology Inventory accuracy validation (Epic 4 Slice 4.3).

Classifies expected versus actual inventory facts and computes precision/recall
for the validation set only — not general product accuracy claims.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InventoryCategory(StrEnum):
    LANGUAGES = "languages"
    FRAMEWORKS = "frameworks"
    BUILD_SYSTEMS = "build_systems"
    DEPENDENCY_ECOSYSTEMS = "dependency_ecosystems"
    RUNTIMES = "runtimes"
    LIBRARIES = "libraries"
    TESTING = "testing"
    VERSIONS = "versions"
    COMPOSITION = "composition"
    APPLICATION_INDICATORS = "application_indicators"


class FactClassification(StrEnum):
    TRUE_POSITIVE = "TRUE_POSITIVE"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    FALSE_NEGATIVE = "FALSE_NEGATIVE"
    AMBIGUOUS = "AMBIGUOUS"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class InventoryVersionExpectation(BaseModel):
    """Required or forbidden version declaration for a named technology."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    version: str | None = None
    version_state: str | None = None  # exact | range | unavailable | any
    evidence_note: str = ""
    rationale: str | None = None


class TechnologyInventoryExpectation(BaseModel):
    """Evidence-authored Technology Inventory expectations for one repository."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    required_languages: tuple[str, ...] = ()
    forbidden_languages: tuple[str, ...] = ()
    required_frameworks: tuple[str, ...] = ()
    forbidden_frameworks: tuple[str, ...] = ()
    required_build_systems: tuple[str, ...] = ()
    forbidden_build_systems: tuple[str, ...] = ()
    required_dependency_ecosystems: tuple[str, ...] = ()
    forbidden_dependency_ecosystems: tuple[str, ...] = ()
    required_runtimes: tuple[str, ...] = ()
    forbidden_runtimes: tuple[str, ...] = ()
    required_libraries: tuple[str, ...] = ()
    forbidden_libraries: tuple[str, ...] = ()
    required_testing: tuple[str, ...] = ()
    forbidden_testing: tuple[str, ...] = ()
    required_versions: tuple[InventoryVersionExpectation, ...] = ()
    forbidden_versions: tuple[InventoryVersionExpectation, ...] = ()
    expected_repository_facts: tuple[str, ...] = ()
    forbidden_repository_facts: tuple[str, ...] = ()
    expected_application_indicators: tuple[str, ...] = ()
    forbidden_application_indicators: tuple[str, ...] = ()
    allowed_ambiguous_facts: tuple[str, ...] = ()
    not_applicable_categories: tuple[str, ...] = ()
    maximum_false_positive_count: int | None = Field(default=None, ge=0)
    minimum_required_detection_count: int | None = Field(default=None, ge=0)
    evidence_notes: str | None = None

    @model_validator(mode="after")
    def _reject_contradictions(self) -> TechnologyInventoryExpectation:
        pairs = (
            (self.required_languages, self.forbidden_languages, "languages"),
            (self.required_frameworks, self.forbidden_frameworks, "frameworks"),
            (self.required_build_systems, self.forbidden_build_systems, "build_systems"),
            (
                self.required_dependency_ecosystems,
                self.forbidden_dependency_ecosystems,
                "dependency_ecosystems",
            ),
            (self.required_runtimes, self.forbidden_runtimes, "runtimes"),
            (self.required_libraries, self.forbidden_libraries, "libraries"),
            (self.required_testing, self.forbidden_testing, "testing"),
            (
                self.expected_repository_facts,
                self.forbidden_repository_facts,
                "repository_facts",
            ),
            (
                self.expected_application_indicators,
                self.forbidden_application_indicators,
                "application_indicators",
            ),
        )
        for required, forbidden, area in pairs:
            overlap = sorted(set(required) & set(forbidden))
            if overlap:
                raise ValueError(f"contradictory {area} inventory expectations: {overlap}")
        required_version_names = {item.name for item in self.required_versions}
        forbidden_version_names = {item.name for item in self.forbidden_versions}
        overlap_versions = sorted(required_version_names & forbidden_version_names)
        if overlap_versions:
            raise ValueError(
                f"contradictory version inventory expectations: {overlap_versions}"
            )
        ambiguous = set(self.allowed_ambiguous_facts)
        for required, _forbidden, area in pairs:
            bad = sorted(set(required) & ambiguous)
            if bad:
                raise ValueError(
                    f"ambiguous facts cannot also be required ({area}): {bad}"
                )
        return self


class ClassifiedFact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    category: str
    classification: FactClassification
    expectation: str
    actual: str
    diagnostic: str


class CategoryMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    category: str
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    ambiguous: int = 0
    not_applicable: int = 0
    precision: float | None = None
    recall: float | None = None
    unavailable_reason: str | None = None


class InventoryValidationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    repository_id: str
    classifications: tuple[ClassifiedFact, ...] = ()
    category_metrics: tuple[CategoryMetrics, ...] = ()
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    ambiguous: int = 0
    precision: float | None = None
    recall: float | None = None
    passed: bool = True
    diagnostics: tuple[str, ...] = ()


class AggregateInventoryMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    repository_count: int = 0
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    ambiguous: int = 0
    precision: float | None = None
    recall: float | None = None
    per_category: tuple[CategoryMetrics, ...] = ()
    per_repository: tuple[InventoryValidationResult, ...] = ()


def compute_precision_recall(
    *,
    true_positives: int,
    false_positives: int,
    false_negatives: int,
) -> tuple[float | None, float | None, str | None]:
    """Return ``(precision, recall, unavailable_reason)``.

    Zero denominators yield ``None`` metrics rather than artificial 0/100.
    """

    precision: float | None
    recall: float | None
    reasons: list[str] = []
    denom_p = true_positives + false_positives
    denom_r = true_positives + false_negatives
    if denom_p == 0:
        precision = None
        reasons.append("precision unavailable: TP+FP=0")
    else:
        precision = true_positives / denom_p
    if denom_r == 0:
        recall = None
        reasons.append("recall unavailable: TP+FN=0")
    else:
        recall = true_positives / denom_r
    return precision, recall, "; ".join(reasons) if reasons else None


def classify_name_sets(
    *,
    category: str,
    required: tuple[str, ...] | list[str],
    forbidden: tuple[str, ...] | list[str],
    actual: tuple[str, ...] | list[str] | set[str],
    ambiguous_allowed: tuple[str, ...] | list[str] = (),
    category_not_applicable: bool = False,
) -> list[ClassifiedFact]:
    """Classify required/forbidden/actual names for one inventory category."""

    if category_not_applicable:
        return [
            ClassifiedFact(
                name="*",
                category=category,
                classification=FactClassification.NOT_APPLICABLE,
                expectation="category not applicable",
                actual=f"actual={sorted(set(actual))}",
                diagnostic="category marked not_applicable",
            )
        ]

    required_set = {_norm(item) for item in required}
    forbidden_set = {_norm(item) for item in forbidden}
    actual_set = {_norm(item) for item in actual if _norm(item)}
    ambiguous_set = {_norm(item) for item in ambiguous_allowed}
    display = {_norm(item): item for item in (*required, *forbidden, *actual, *ambiguous_allowed)}

    facts: list[ClassifiedFact] = []

    for name in sorted(required_set):
        label = display.get(name, name)
        if name in actual_set:
            facts.append(
                ClassifiedFact(
                    name=label,
                    category=category,
                    classification=FactClassification.TRUE_POSITIVE,
                    expectation=f"required {label}",
                    actual="present",
                    diagnostic="required detection matched",
                )
            )
        else:
            facts.append(
                ClassifiedFact(
                    name=label,
                    category=category,
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=f"required {label}",
                    actual="absent",
                    diagnostic="required detection missing",
                )
            )

    for name in sorted(forbidden_set):
        label = display.get(name, name)
        if name in actual_set:
            facts.append(
                ClassifiedFact(
                    name=label,
                    category=category,
                    classification=FactClassification.FALSE_POSITIVE,
                    expectation=f"forbidden {label}",
                    actual="present",
                    diagnostic="forbidden detection present",
                )
            )

    for name in sorted(actual_set & ambiguous_set):
        label = display.get(name, name)
        facts.append(
            ClassifiedFact(
                name=label,
                category=category,
                classification=FactClassification.AMBIGUOUS,
                expectation="allowed ambiguous",
                actual="present",
                diagnostic="ambiguous fact excluded from TP/FP scoring",
            )
        )

    return facts


def metrics_from_classifications(
    *,
    category: str,
    classifications: list[ClassifiedFact] | tuple[ClassifiedFact, ...],
) -> CategoryMetrics:
    scoped = [item for item in classifications if item.category == category]
    tp = sum(1 for item in scoped if item.classification is FactClassification.TRUE_POSITIVE)
    fp = sum(1 for item in scoped if item.classification is FactClassification.FALSE_POSITIVE)
    fn = sum(1 for item in scoped if item.classification is FactClassification.FALSE_NEGATIVE)
    amb = sum(1 for item in scoped if item.classification is FactClassification.AMBIGUOUS)
    na = sum(1 for item in scoped if item.classification is FactClassification.NOT_APPLICABLE)
    if na and not (tp or fp or fn):
        return CategoryMetrics(
            category=category,
            not_applicable=na,
            unavailable_reason="category not applicable",
        )
    precision, recall, reason = compute_precision_recall(
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
    )
    return CategoryMetrics(
        category=category,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        ambiguous=amb,
        not_applicable=na,
        precision=precision,
        recall=recall,
        unavailable_reason=reason,
    )


def validate_technology_inventory(
    *,
    repository_id: str,
    expectation: TechnologyInventoryExpectation,
    actual_by_category: dict[str, tuple[str, ...]],
    actual_versions: dict[str, str | None] | None = None,
) -> InventoryValidationResult:
    """Compare evidence-backed inventory expectations to normalized actual facts."""

    actual_versions = actual_versions or {}
    na = {_norm(item) for item in expectation.not_applicable_categories}
    ambiguous = expectation.allowed_ambiguous_facts
    classifications: list[ClassifiedFact] = []

    category_specs: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
        (
            InventoryCategory.LANGUAGES.value,
            expectation.required_languages,
            expectation.forbidden_languages,
        ),
        (
            InventoryCategory.FRAMEWORKS.value,
            expectation.required_frameworks,
            expectation.forbidden_frameworks,
        ),
        (
            InventoryCategory.BUILD_SYSTEMS.value,
            expectation.required_build_systems,
            expectation.forbidden_build_systems,
        ),
        (
            InventoryCategory.DEPENDENCY_ECOSYSTEMS.value,
            expectation.required_dependency_ecosystems,
            expectation.forbidden_dependency_ecosystems,
        ),
        (
            InventoryCategory.RUNTIMES.value,
            expectation.required_runtimes,
            expectation.forbidden_runtimes,
        ),
        (
            InventoryCategory.LIBRARIES.value,
            expectation.required_libraries,
            expectation.forbidden_libraries,
        ),
        (
            InventoryCategory.TESTING.value,
            expectation.required_testing,
            expectation.forbidden_testing,
        ),
        (
            InventoryCategory.COMPOSITION.value,
            expectation.expected_repository_facts,
            expectation.forbidden_repository_facts,
        ),
        (
            InventoryCategory.APPLICATION_INDICATORS.value,
            expectation.expected_application_indicators,
            expectation.forbidden_application_indicators,
        ),
    )

    for category, required, forbidden in category_specs:
        classifications.extend(
            classify_name_sets(
                category=category,
                required=required,
                forbidden=forbidden,
                actual=actual_by_category.get(category, ()),
                ambiguous_allowed=ambiguous,
                category_not_applicable=category in na or _norm(category) in na,
            )
        )

    # Version checks
    if InventoryCategory.VERSIONS.value not in na and _norm("versions") not in na:
        for item in expectation.required_versions:
            actual_version = actual_versions.get(item.name)
            ok = _version_matches(item, actual_version)
            classifications.append(
                ClassifiedFact(
                    name=item.name,
                    category=InventoryCategory.VERSIONS.value,
                    classification=(
                        FactClassification.TRUE_POSITIVE
                        if ok
                        else FactClassification.FALSE_NEGATIVE
                    ),
                    expectation=_version_expectation_text(item),
                    actual=repr(actual_version),
                    diagnostic=item.evidence_note or item.rationale or "version check",
                )
            )
        for item in expectation.forbidden_versions:
            actual_version = actual_versions.get(item.name)
            if actual_version and _version_matches(item, actual_version):
                classifications.append(
                    ClassifiedFact(
                        name=item.name,
                        category=InventoryCategory.VERSIONS.value,
                        classification=FactClassification.FALSE_POSITIVE,
                        expectation=_version_expectation_text(item),
                        actual=repr(actual_version),
                        diagnostic="forbidden version present",
                    )
                )

    category_metrics = tuple(
        metrics_from_classifications(category=category.value, classifications=classifications)
        for category in InventoryCategory
    )

    tp = sum(1 for item in classifications if item.classification is FactClassification.TRUE_POSITIVE)
    fp = sum(1 for item in classifications if item.classification is FactClassification.FALSE_POSITIVE)
    fn = sum(1 for item in classifications if item.classification is FactClassification.FALSE_NEGATIVE)
    amb = sum(1 for item in classifications if item.classification is FactClassification.AMBIGUOUS)
    precision, recall, _reason = compute_precision_recall(
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
    )

    diagnostics: list[str] = []
    for item in classifications:
        if item.classification in {
            FactClassification.FALSE_POSITIVE,
            FactClassification.FALSE_NEGATIVE,
        }:
            diagnostics.append(
                f"{item.category}:{item.classification.value}:{item.name}:{item.diagnostic}"
            )

    passed = fp == 0 and fn == 0
    if expectation.maximum_false_positive_count is not None:
        passed = passed and fp <= expectation.maximum_false_positive_count
    if expectation.minimum_required_detection_count is not None:
        passed = passed and tp >= expectation.minimum_required_detection_count

    return InventoryValidationResult(
        repository_id=repository_id,
        classifications=tuple(classifications),
        category_metrics=category_metrics,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        ambiguous=amb,
        precision=precision,
        recall=recall,
        passed=passed,
        diagnostics=tuple(diagnostics),
    )


def aggregate_inventory_results(
    results: list[InventoryValidationResult] | tuple[InventoryValidationResult, ...],
) -> AggregateInventoryMetrics:
    results_t = tuple(results)
    tp = sum(item.true_positives for item in results_t)
    fp = sum(item.false_positives for item in results_t)
    fn = sum(item.false_negatives for item in results_t)
    amb = sum(item.ambiguous for item in results_t)
    precision, recall, _ = compute_precision_recall(
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
    )

    by_category: dict[str, list[int]] = {
        category.value: [0, 0, 0, 0] for category in InventoryCategory
    }
    for result in results_t:
        for metrics in result.category_metrics:
            bucket = by_category.setdefault(metrics.category, [0, 0, 0, 0])
            bucket[0] += metrics.true_positives
            bucket[1] += metrics.false_positives
            bucket[2] += metrics.false_negatives
            bucket[3] += metrics.ambiguous

    per_category: list[CategoryMetrics] = []
    for category, (ctp, cfp, cfn, camb) in sorted(by_category.items()):
        cprec, crec, creason = compute_precision_recall(
            true_positives=ctp,
            false_positives=cfp,
            false_negatives=cfn,
        )
        per_category.append(
            CategoryMetrics(
                category=category,
                true_positives=ctp,
                false_positives=cfp,
                false_negatives=cfn,
                ambiguous=camb,
                precision=cprec,
                recall=crec,
                unavailable_reason=creason,
            )
        )

    return AggregateInventoryMetrics(
        repository_count=len(results_t),
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        ambiguous=amb,
        precision=precision,
        recall=recall,
        per_category=tuple(per_category),
        per_repository=results_t,
    )


def inventory_result_to_safe_dict(result: InventoryValidationResult) -> dict[str, Any]:
    """JSON-serializable inventory result without source bodies or absolute paths."""

    return result.model_dump(mode="json")


def _norm(value: str) -> str:
    return value.strip().lower()


def _version_expectation_text(item: InventoryVersionExpectation) -> str:
    parts = [f"name={item.name}"]
    if item.version is not None:
        parts.append(f"version={item.version}")
    if item.version_state is not None:
        parts.append(f"state={item.version_state}")
    return ",".join(parts)


def _version_matches(item: InventoryVersionExpectation, actual: str | None) -> bool:
    state = (item.version_state or "any").lower()
    if state == "unavailable":
        return actual is None or str(actual).strip() == ""
    if actual is None or str(actual).strip() == "":
        return False
    text = str(actual).strip()
    if state == "range":
        markers = ("^", "~", "*", ">=", "<=", ">", "<", "||", " - ", "x")
        if item.version:
            return item.version in text or text == item.version
        return any(marker in text for marker in markers)
    if state == "exact":
        if item.version is None:
            return bool(text) and not any(m in text for m in ("^", "~", "*", ">", "<"))
        return text == item.version
    # any / default: require non-empty; if expected version provided, substring/equality
    if item.version is None:
        return True
    return text == item.version or item.version in text
