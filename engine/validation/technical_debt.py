"""Technical Debt precision validation (Epic 4 Slice 4.6).

Evidence-authored Technical Debt expectations, TP/FP/FN classification, and
precision/recall for the validation set only.
"""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from validation.inventory import (
    FactClassification,
    compute_precision_recall,
)


class TechnicalDebtMetric(StrEnum):
    PHYSICAL_LINE_COUNT = "physical_line_count"
    BRANCH_POINT_COUNT = "branch_point_count"
    MAX_NESTING_DEPTH = "max_nesting_depth"
    PARAMETER_COUNT = "parameter_count"
    OTHER = "other"


class TechnicalDebtScope(StrEnum):
    CALLABLE = "callable"
    TYPE = "type"
    FILE = "file"
    OTHER = "other"


_RULE_METRIC: dict[str, TechnicalDebtMetric] = {
    "technical_debt.large-callable": TechnicalDebtMetric.PHYSICAL_LINE_COUNT,
    "technical_debt.excessive-branching": TechnicalDebtMetric.BRANCH_POINT_COUNT,
    "technical_debt.deep-nesting": TechnicalDebtMetric.MAX_NESTING_DEPTH,
    "technical_debt.excessive-parameters": TechnicalDebtMetric.PARAMETER_COUNT,
    "technical_debt.oversized-type": TechnicalDebtMetric.PHYSICAL_LINE_COUNT,
}

_RULE_SCOPE: dict[str, TechnicalDebtScope] = {
    "technical_debt.large-callable": TechnicalDebtScope.CALLABLE,
    "technical_debt.excessive-branching": TechnicalDebtScope.CALLABLE,
    "technical_debt.deep-nesting": TechnicalDebtScope.CALLABLE,
    "technical_debt.excessive-parameters": TechnicalDebtScope.CALLABLE,
    "technical_debt.oversized-type": TechnicalDebtScope.TYPE,
}


class TechnicalDebtFindingExpectation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    path: str | None = None
    path_pattern: str | None = None
    symbol: str | None = None
    symbol_pattern: str | None = None
    scope: TechnicalDebtScope | None = None
    measured_value: int | float | None = None
    threshold: int | float | None = None
    threshold_operator: str | None = None
    severity: str | None = None
    confidence: str | None = None
    expected_count: int | None = Field(default=None, ge=0)
    rationale: str = ""


class TechnicalDebtRuleCountRange(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    minimum: int | None = Field(default=None, ge=0)
    maximum: int | None = Field(default=None, ge=0)
    exact: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _validate_range(self) -> TechnicalDebtRuleCountRange:
        if self.exact is not None and (self.minimum is not None or self.maximum is not None):
            raise ValueError("exact cannot be combined with minimum/maximum")
        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ValueError("minimum cannot exceed maximum")
        if self.exact is None and self.minimum is None and self.maximum is None:
            raise ValueError("count range requires exact, minimum, and/or maximum")
        return self

    def contains(self, value: int) -> bool:
        if self.exact is not None:
            return value == self.exact
        if self.minimum is not None and value < self.minimum:
            return False
        if self.maximum is not None and value > self.maximum:
            return False
        return True

    def describe(self) -> str:
        if self.exact is not None:
            return f"exact={self.exact}"
        parts: list[str] = []
        if self.minimum is not None:
            parts.append(f"min={self.minimum}")
        if self.maximum is not None:
            parts.append(f"max={self.maximum}")
        return ",".join(parts)


class TechnicalDebtExpectation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    required_findings: tuple[TechnicalDebtFindingExpectation, ...] = ()
    forbidden_findings: tuple[TechnicalDebtFindingExpectation, ...] = ()
    allowed_findings: tuple[TechnicalDebtFindingExpectation, ...] = ()
    expected_rule_ids: tuple[str, ...] = ()
    forbidden_rule_ids: tuple[str, ...] = ()
    expected_rule_count_ranges: tuple[TechnicalDebtRuleCountRange, ...] = ()
    maximum_false_positive_count: int | None = Field(default=None, ge=0)
    expected_unavailable_metrics: tuple[str, ...] = ()
    expected_unsupported_metrics: tuple[str, ...] = ()
    expected_limitations: tuple[str, ...] = ()
    forbidden_conclusions: tuple[str, ...] = ()
    not_applicable_rule_ids: tuple[str, ...] = ()
    evidence_notes: str | None = None

    @model_validator(mode="after")
    def _reject_contradictions(self) -> TechnicalDebtExpectation:
        required_any = {item.rule_id for item in self.required_findings} | set(
            self.expected_rule_ids
        )
        overlap = sorted(required_any & set(self.forbidden_rule_ids))
        if overlap:
            raise ValueError(f"contradictory technical debt rule expectations: {overlap}")
        required_global = set(self.expected_rule_ids) | {
            item.rule_id
            for item in self.required_findings
            if not item.path
            and not item.path_pattern
            and not item.symbol
            and not item.symbol_pattern
        }
        forbidden_global = set(self.forbidden_rule_ids) | {
            item.rule_id
            for item in self.forbidden_findings
            if not item.path
            and not item.path_pattern
            and not item.symbol
            and not item.symbol_pattern
        }
        overlap2 = sorted(required_global & forbidden_global)
        if overlap2:
            raise ValueError(f"contradictory technical debt rule expectations: {overlap2}")
        return self


class TechnicalDebtFindingActual(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    finding_id: str | None = None
    path: str | None = None
    symbol: str | None = None
    scope: TechnicalDebtScope = TechnicalDebtScope.OTHER
    metric: TechnicalDebtMetric = TechnicalDebtMetric.OTHER
    measured_value: int | float | None = None
    threshold: int | float | None = None
    threshold_operator: str | None = None
    comparison_result: str | None = None
    severity: str | None = None
    confidence: str | None = None
    classification: str | None = None
    evidence_ids: tuple[str, ...] = ()


class ClassifiedTechnicalDebtFact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    rule_id: str
    classification: FactClassification
    expectation: str
    actual: str
    diagnostic: str
    metric: TechnicalDebtMetric = TechnicalDebtMetric.OTHER
    scope: TechnicalDebtScope = TechnicalDebtScope.OTHER
    path: str | None = None


class TechnicalDebtRuleMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    metric: TechnicalDebtMetric = TechnicalDebtMetric.OTHER
    scope: TechnicalDebtScope = TechnicalDebtScope.OTHER
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    ambiguous: int = 0
    precision: float | None = None
    recall: float | None = None
    unavailable_reason: str | None = None


class TechnicalDebtValidationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    repository_id: str
    classifications: tuple[ClassifiedTechnicalDebtFact, ...] = ()
    per_rule_metrics: tuple[TechnicalDebtRuleMetrics, ...] = ()
    per_metric_metrics: tuple[TechnicalDebtRuleMetrics, ...] = ()
    per_scope_metrics: tuple[TechnicalDebtRuleMetrics, ...] = ()
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    ambiguous: int = 0
    precision: float | None = None
    recall: float | None = None
    unsupported_claim_failures: tuple[str, ...] = ()
    measurement_failures: tuple[str, ...] = ()
    context_failures: tuple[str, ...] = ()
    passed: bool = True
    diagnostics: tuple[str, ...] = ()


class AggregateTechnicalDebtMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    repository_count: int = 0
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    ambiguous: int = 0
    precision: float | None = None
    recall: float | None = None
    per_rule: tuple[TechnicalDebtRuleMetrics, ...] = ()
    per_metric: tuple[TechnicalDebtRuleMetrics, ...] = ()
    per_scope: tuple[TechnicalDebtRuleMetrics, ...] = ()
    per_repository: tuple[TechnicalDebtValidationResult, ...] = ()


def metric_for_rule(rule_id: str) -> TechnicalDebtMetric:
    return _RULE_METRIC.get(rule_id, TechnicalDebtMetric.OTHER)


def scope_for_rule(rule_id: str) -> TechnicalDebtScope:
    return _RULE_SCOPE.get(rule_id, TechnicalDebtScope.OTHER)


def extract_technical_debt_findings(
    findings: list[Any] | tuple[Any, ...],
) -> tuple[TechnicalDebtFindingActual, ...]:
    rows: list[TechnicalDebtFindingActual] = []
    for item in findings:
        if not isinstance(item, dict):
            continue
        rule_id = str(item.get("rule_id") or "").strip()
        if not rule_id.startswith("technical_debt."):
            continue
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        path = (
            metadata.get("path")
            or item.get("path")
            or item.get("file")
            or _first_evidence_path(item.get("evidence"))
        )
        symbol = (
            metadata.get("subject_keys")
            if isinstance(metadata.get("subject_keys"), str)
            else None
        )
        if isinstance(metadata.get("subject_keys"), (list, tuple)) and metadata["subject_keys"]:
            # subject_keys typically (path, signature)
            parts = [str(part) for part in metadata["subject_keys"]]
            symbol = parts[-1] if parts else None
            if path is None and parts:
                path = parts[0]
        measurement = _first_measurement(item)
        evidence_ids: list[str] = []
        for ref in item.get("evidence_refs") or []:
            if isinstance(ref, dict) and ref.get("evidence_id"):
                evidence_ids.append(str(ref["evidence_id"]))
        for evidence in item.get("evidence") or []:
            if isinstance(evidence, dict):
                eid = evidence.get("source_id") or evidence.get("evidence_id") or evidence.get("id")
                if eid:
                    evidence_ids.append(str(eid))
        if item.get("primary_evidence_id"):
            evidence_ids.append(str(item["primary_evidence_id"]))
        metric_name = (
            (measurement or {}).get("metric_name")
            or metadata.get("metric")
            or metric_for_rule(rule_id).value
        )
        scope_raw = (measurement or {}).get("scope") or scope_for_rule(rule_id).value
        rows.append(
            TechnicalDebtFindingActual(
                rule_id=rule_id,
                finding_id=str(item.get("id")) if item.get("id") else None,
                path=str(path) if path else None,
                symbol=str(symbol) if symbol else None,
                scope=_parse_scope(scope_raw),
                metric=_parse_metric(metric_name),
                measured_value=_as_number(
                    (measurement or {}).get("measured_value") or metadata.get("value")
                ),
                threshold=_as_number(
                    (measurement or {}).get("threshold") or metadata.get("threshold")
                ),
                threshold_operator=(
                    str((measurement or {}).get("threshold_operator") or "gt").lower()
                ),
                comparison_result=(
                    str((measurement or {}).get("comparison_result")).lower()
                    if (measurement or {}).get("comparison_result")
                    else None
                ),
                severity=str(item.get("severity")).lower() if item.get("severity") else None,
                confidence=(
                    str(metadata.get("confidence") or item.get("confidence")).lower()
                    if (metadata.get("confidence") or item.get("confidence"))
                    else None
                ),
                classification=(
                    str(metadata.get("classification")).lower()
                    if metadata.get("classification")
                    else None
                ),
                evidence_ids=tuple(sorted(set(evidence_ids))),
            )
        )
    return tuple(rows)


def validate_technical_debt_precision(
    *,
    repository_id: str,
    expectation: TechnicalDebtExpectation,
    actual_findings: tuple[TechnicalDebtFindingActual, ...] | list[TechnicalDebtFindingActual],
    artifact_texts: dict[str, str] | None = None,
) -> TechnicalDebtValidationResult:
    actual = tuple(actual_findings)
    classifications: list[ClassifiedTechnicalDebtFact] = []
    allowed_rule_ids = {item.rule_id for item in expectation.allowed_findings}
    structured_required = {item.rule_id for item in expectation.required_findings}

    for req in expectation.required_findings:
        matches = [item for item in actual if _finding_matches(req, item)]
        expected_count = req.expected_count if req.expected_count is not None else 1
        metric = metric_for_rule(req.rule_id)
        scope = req.scope or scope_for_rule(req.rule_id)
        if len(matches) >= expected_count and all(
            _measurement_matches(req, match) for match in matches[:expected_count]
        ):
            classifications.append(
                ClassifiedTechnicalDebtFact(
                    name=req.rule_id,
                    rule_id=req.rule_id,
                    classification=FactClassification.TRUE_POSITIVE,
                    expectation=_expect_text(req),
                    actual=f"count={len(matches)}",
                    diagnostic=req.rationale or "required technical debt finding matched",
                    metric=metric,
                    scope=scope,
                    path=req.path,
                )
            )
        else:
            classifications.append(
                ClassifiedTechnicalDebtFact(
                    name=req.rule_id,
                    rule_id=req.rule_id,
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=_expect_text(req),
                    actual=f"count={len(matches)}",
                    diagnostic=req.rationale or "required technical debt finding missing",
                    metric=metric,
                    scope=scope,
                    path=req.path,
                )
            )

    for rule_id in expectation.expected_rule_ids:
        if rule_id in structured_required:
            continue
        present = [item for item in actual if item.rule_id == rule_id]
        if present:
            classifications.append(
                ClassifiedTechnicalDebtFact(
                    name=rule_id,
                    rule_id=rule_id,
                    classification=FactClassification.TRUE_POSITIVE,
                    expectation=f"required rule {rule_id}",
                    actual=f"count={len(present)}",
                    diagnostic="required rule present",
                    metric=metric_for_rule(rule_id),
                    scope=scope_for_rule(rule_id),
                )
            )
        else:
            classifications.append(
                ClassifiedTechnicalDebtFact(
                    name=rule_id,
                    rule_id=rule_id,
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=f"required rule {rule_id}",
                    actual="absent",
                    diagnostic="required rule missing",
                    metric=metric_for_rule(rule_id),
                    scope=scope_for_rule(rule_id),
                )
            )

    for forb in expectation.forbidden_findings:
        matches = [item for item in actual if _finding_matches(forb, item)]
        for match in matches:
            classifications.append(
                ClassifiedTechnicalDebtFact(
                    name=forb.rule_id,
                    rule_id=forb.rule_id,
                    classification=FactClassification.FALSE_POSITIVE,
                    expectation=_expect_text(forb),
                    actual=f"path={match.path!r} symbol={match.symbol!r}",
                    diagnostic=forb.rationale or "forbidden technical debt finding present",
                    metric=metric_for_rule(forb.rule_id),
                    scope=forb.scope or scope_for_rule(forb.rule_id),
                    path=match.path,
                )
            )

    for rule_id in expectation.forbidden_rule_ids:
        matches = [item for item in actual if item.rule_id == rule_id]
        specific = [
            forb for forb in expectation.forbidden_findings if forb.rule_id == rule_id
        ]
        for match in matches:
            if specific and any(_finding_matches(forb, match) for forb in specific):
                continue
            if match.rule_id in allowed_rule_ids:
                classifications.append(
                    ClassifiedTechnicalDebtFact(
                        name=rule_id,
                        rule_id=rule_id,
                        classification=FactClassification.AMBIGUOUS,
                        expectation="allowed overlap",
                        actual=f"path={match.path!r}",
                        diagnostic="allowed finding excluded from FP scoring",
                        metric=metric_for_rule(rule_id),
                        scope=scope_for_rule(rule_id),
                        path=match.path,
                    )
                )
            else:
                classifications.append(
                    ClassifiedTechnicalDebtFact(
                        name=rule_id,
                        rule_id=rule_id,
                        classification=FactClassification.FALSE_POSITIVE,
                        expectation=f"forbidden rule {rule_id}",
                        actual=f"path={match.path!r}",
                        diagnostic="forbidden rule present",
                        metric=metric_for_rule(rule_id),
                        scope=scope_for_rule(rule_id),
                        path=match.path,
                    )
                )

    for allowed in expectation.allowed_findings:
        matches = [item for item in actual if _finding_matches(allowed, item)]
        if matches and allowed.rule_id not in structured_required:
            classifications.append(
                ClassifiedTechnicalDebtFact(
                    name=allowed.rule_id,
                    rule_id=allowed.rule_id,
                    classification=FactClassification.AMBIGUOUS,
                    expectation=allowed.rationale or "allowed finding",
                    actual=f"count={len(matches)}",
                    diagnostic="allowed finding not scored as TP",
                    metric=metric_for_rule(allowed.rule_id),
                    scope=allowed.scope or scope_for_rule(allowed.rule_id),
                    path=allowed.path,
                )
            )

    for range_spec in expectation.expected_rule_count_ranges:
        count = sum(1 for item in actual if item.rule_id == range_spec.rule_id)
        if not range_spec.contains(count):
            classifications.append(
                ClassifiedTechnicalDebtFact(
                    name=range_spec.rule_id,
                    rule_id=range_spec.rule_id,
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=f"count {range_spec.describe()}",
                    actual=f"count={count}",
                    diagnostic="rule count outside range",
                    metric=metric_for_rule(range_spec.rule_id),
                    scope=scope_for_rule(range_spec.rule_id),
                )
            )

    for rule_id in expectation.not_applicable_rule_ids:
        if any(item.rule_id == rule_id for item in actual):
            classifications.append(
                ClassifiedTechnicalDebtFact(
                    name=rule_id,
                    rule_id=rule_id,
                    classification=FactClassification.FALSE_POSITIVE,
                    expectation="not applicable",
                    actual="present",
                    diagnostic="not-applicable rule emitted a finding",
                    metric=metric_for_rule(rule_id),
                    scope=scope_for_rule(rule_id),
                )
            )
        else:
            classifications.append(
                ClassifiedTechnicalDebtFact(
                    name=rule_id,
                    rule_id=rule_id,
                    classification=FactClassification.NOT_APPLICABLE,
                    expectation="not applicable",
                    actual="absent",
                    diagnostic="rule marked not_applicable",
                    metric=metric_for_rule(rule_id),
                    scope=scope_for_rule(rule_id),
                )
            )

    measurement_failures: list[str] = []
    context_failures: list[str] = []
    for item in actual:
        if item.path and (item.path.startswith("/") or item.path.startswith("\\")):
            measurement_failures.append(f"absolute_path:{item.rule_id}:{item.path}")
        if item.measured_value is None or item.threshold is None:
            measurement_failures.append(f"missing_measurement:{item.rule_id}:{item.finding_id}")
        elif item.threshold_operator in {"gt", ">"} and not (
            item.measured_value > item.threshold
        ):
            measurement_failures.append(
                f"threshold_not_exceeded:{item.rule_id}:{item.measured_value}<={item.threshold}"
            )
        if item.path and _looks_non_production_path(item.path):
            context_failures.append(f"non_production_path:{item.rule_id}:{item.path}")
        if item.classification and item.classification not in {"source", "production", ""}:
            if item.classification in {"test", "fixture", "generated", "vendor", "example"}:
                context_failures.append(
                    f"non_production_classification:{item.rule_id}:{item.classification}"
                )

    unsupported: list[str] = []
    artifact_texts = artifact_texts or {}
    for claim in expectation.forbidden_conclusions:
        needle = claim.lower()
        for name, text in artifact_texts.items():
            lowered = text.lower()
            if needle in lowered and not _is_disclaimer_negation(lowered, needle):
                unsupported.append(f"{name}:{claim}")

    tp = sum(1 for item in classifications if item.classification is FactClassification.TRUE_POSITIVE)
    fp = sum(1 for item in classifications if item.classification is FactClassification.FALSE_POSITIVE)
    fn = sum(1 for item in classifications if item.classification is FactClassification.FALSE_NEGATIVE)
    amb = sum(1 for item in classifications if item.classification is FactClassification.AMBIGUOUS)
    precision, recall, _ = compute_precision_recall(
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
    )
    per_rule = _per_rule_metrics(classifications)
    per_metric = _per_dimension_metrics(classifications, key="metric")
    per_scope = _per_dimension_metrics(classifications, key="scope")
    diagnostics = [
        f"{item.classification.value}:{item.rule_id}:{item.diagnostic}"
        for item in classifications
        if item.classification
        in {FactClassification.FALSE_POSITIVE, FactClassification.FALSE_NEGATIVE}
    ]
    diagnostics.extend(f"unsupported:{item}" for item in unsupported)
    diagnostics.extend(f"measurement:{item}" for item in measurement_failures)
    diagnostics.extend(f"context:{item}" for item in context_failures)

    passed = (
        fp == 0
        and fn == 0
        and not unsupported
        and not measurement_failures
        and not context_failures
    )
    if expectation.maximum_false_positive_count is not None:
        passed = passed and fp <= expectation.maximum_false_positive_count

    return TechnicalDebtValidationResult(
        repository_id=repository_id,
        classifications=tuple(classifications),
        per_rule_metrics=per_rule,
        per_metric_metrics=per_metric,
        per_scope_metrics=per_scope,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        ambiguous=amb,
        precision=precision,
        recall=recall,
        unsupported_claim_failures=tuple(unsupported),
        measurement_failures=tuple(measurement_failures),
        context_failures=tuple(context_failures),
        passed=passed,
        diagnostics=tuple(diagnostics),
    )


def aggregate_technical_debt_results(
    results: list[TechnicalDebtValidationResult] | tuple[TechnicalDebtValidationResult, ...],
) -> AggregateTechnicalDebtMetrics:
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
    by_rule: dict[str, list[Any]] = {}
    by_metric: dict[str, list[int]] = {}
    by_scope: dict[str, list[int]] = {}
    for result in results_t:
        for metrics in result.per_rule_metrics:
            bucket = by_rule.setdefault(
                metrics.rule_id, [0, 0, 0, 0, metrics.metric, metrics.scope]
            )
            bucket[0] += metrics.true_positives
            bucket[1] += metrics.false_positives
            bucket[2] += metrics.false_negatives
            bucket[3] += metrics.ambiguous
        for metrics in result.per_metric_metrics:
            bucket = by_metric.setdefault(metrics.rule_id, [0, 0, 0, 0])
            bucket[0] += metrics.true_positives
            bucket[1] += metrics.false_positives
            bucket[2] += metrics.false_negatives
            bucket[3] += metrics.ambiguous
        for metrics in result.per_scope_metrics:
            bucket = by_scope.setdefault(metrics.rule_id, [0, 0, 0, 0])
            bucket[0] += metrics.true_positives
            bucket[1] += metrics.false_positives
            bucket[2] += metrics.false_negatives
            bucket[3] += metrics.ambiguous
    per_rule = []
    for rule_id, (rtp, rfp, rfn, ramb, metric, scope) in sorted(by_rule.items()):
        rprec, rrec, rreason = compute_precision_recall(
            true_positives=rtp, false_positives=rfp, false_negatives=rfn
        )
        per_rule.append(
            TechnicalDebtRuleMetrics(
                rule_id=rule_id,
                metric=metric,
                scope=scope,
                true_positives=rtp,
                false_positives=rfp,
                false_negatives=rfn,
                ambiguous=ramb,
                precision=rprec,
                recall=rrec,
                unavailable_reason=rreason,
            )
        )
    per_metric = _aggregate_named(by_metric, kind="metric")
    per_scope = _aggregate_named(by_scope, kind="scope")
    return AggregateTechnicalDebtMetrics(
        repository_count=len(results_t),
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        ambiguous=amb,
        precision=precision,
        recall=recall,
        per_rule=tuple(per_rule),
        per_metric=tuple(per_metric),
        per_scope=tuple(per_scope),
        per_repository=results_t,
    )


def _finding_matches(
    expectation: TechnicalDebtFindingExpectation,
    actual: TechnicalDebtFindingActual,
) -> bool:
    if actual.rule_id != expectation.rule_id:
        return False
    if expectation.path and _norm_path(actual.path or "") != _norm_path(expectation.path):
        return False
    if expectation.path_pattern:
        if not actual.path or not re.search(expectation.path_pattern, actual.path):
            return False
    if expectation.symbol and _norm(actual.symbol or "") != _norm(expectation.symbol):
        return False
    if expectation.symbol_pattern:
        if not actual.symbol or not re.search(expectation.symbol_pattern, actual.symbol):
            return False
    if expectation.severity and _norm(actual.severity or "") != _norm(expectation.severity):
        return False
    if expectation.scope and actual.scope is not expectation.scope:
        return False
    return True


def _measurement_matches(
    expectation: TechnicalDebtFindingExpectation,
    actual: TechnicalDebtFindingActual,
) -> bool:
    if expectation.measured_value is not None and actual.measured_value != expectation.measured_value:
        return False
    if expectation.threshold is not None and actual.threshold != expectation.threshold:
        return False
    if expectation.threshold_operator is not None:
        if _norm(actual.threshold_operator or "") != _norm(expectation.threshold_operator):
            return False
    return True


def _expect_text(item: TechnicalDebtFindingExpectation) -> str:
    parts = [f"rule={item.rule_id}"]
    if item.path:
        parts.append(f"path={item.path}")
    if item.symbol:
        parts.append(f"symbol={item.symbol}")
    if item.measured_value is not None:
        parts.append(f"value={item.measured_value}")
    if item.threshold is not None:
        parts.append(f"threshold={item.threshold}")
    return ",".join(parts)


def _per_rule_metrics(
    classifications: list[ClassifiedTechnicalDebtFact],
) -> tuple[TechnicalDebtRuleMetrics, ...]:
    rules = sorted({item.rule_id for item in classifications})
    metrics: list[TechnicalDebtRuleMetrics] = []
    for rule_id in rules:
        scoped = [item for item in classifications if item.rule_id == rule_id]
        tp = sum(1 for item in scoped if item.classification is FactClassification.TRUE_POSITIVE)
        fp = sum(1 for item in scoped if item.classification is FactClassification.FALSE_POSITIVE)
        fn = sum(1 for item in scoped if item.classification is FactClassification.FALSE_NEGATIVE)
        amb = sum(1 for item in scoped if item.classification is FactClassification.AMBIGUOUS)
        precision, recall, reason = compute_precision_recall(
            true_positives=tp, false_positives=fp, false_negatives=fn
        )
        metrics.append(
            TechnicalDebtRuleMetrics(
                rule_id=rule_id,
                metric=scoped[0].metric if scoped else metric_for_rule(rule_id),
                scope=scoped[0].scope if scoped else scope_for_rule(rule_id),
                true_positives=tp,
                false_positives=fp,
                false_negatives=fn,
                ambiguous=amb,
                precision=precision,
                recall=recall,
                unavailable_reason=reason,
            )
        )
    return tuple(metrics)


def _per_dimension_metrics(
    classifications: list[ClassifiedTechnicalDebtFact],
    *,
    key: str,
) -> tuple[TechnicalDebtRuleMetrics, ...]:
    values = sorted({getattr(item, key).value for item in classifications})
    metrics: list[TechnicalDebtRuleMetrics] = []
    for value in values:
        scoped = [item for item in classifications if getattr(item, key).value == value]
        tp = sum(1 for item in scoped if item.classification is FactClassification.TRUE_POSITIVE)
        fp = sum(1 for item in scoped if item.classification is FactClassification.FALSE_POSITIVE)
        fn = sum(1 for item in scoped if item.classification is FactClassification.FALSE_NEGATIVE)
        amb = sum(1 for item in scoped if item.classification is FactClassification.AMBIGUOUS)
        precision, recall, reason = compute_precision_recall(
            true_positives=tp, false_positives=fp, false_negatives=fn
        )
        metrics.append(
            TechnicalDebtRuleMetrics(
                rule_id=value,
                metric=TechnicalDebtMetric(value)
                if key == "metric" and value in TechnicalDebtMetric._value2member_map_
                else TechnicalDebtMetric.OTHER,
                scope=TechnicalDebtScope(value)
                if key == "scope" and value in TechnicalDebtScope._value2member_map_
                else TechnicalDebtScope.OTHER,
                true_positives=tp,
                false_positives=fp,
                false_negatives=fn,
                ambiguous=amb,
                precision=precision,
                recall=recall,
                unavailable_reason=reason,
            )
        )
    return tuple(metrics)


def _aggregate_named(
    buckets: dict[str, list[int]],
    *,
    kind: str,
) -> list[TechnicalDebtRuleMetrics]:
    rows: list[TechnicalDebtRuleMetrics] = []
    for name, (tp, fp, fn, amb) in sorted(buckets.items()):
        precision, recall, reason = compute_precision_recall(
            true_positives=tp, false_positives=fp, false_negatives=fn
        )
        rows.append(
            TechnicalDebtRuleMetrics(
                rule_id=name,
                metric=TechnicalDebtMetric(name)
                if kind == "metric" and name in TechnicalDebtMetric._value2member_map_
                else TechnicalDebtMetric.OTHER,
                scope=TechnicalDebtScope(name)
                if kind == "scope" and name in TechnicalDebtScope._value2member_map_
                else TechnicalDebtScope.OTHER,
                true_positives=tp,
                false_positives=fp,
                false_negatives=fn,
                ambiguous=amb,
                precision=precision,
                recall=recall,
                unavailable_reason=reason,
            )
        )
    return rows


def _first_measurement(item: dict[str, Any]) -> dict[str, Any] | None:
    for ref in item.get("evidence_refs") or []:
        if isinstance(ref, dict) and isinstance(ref.get("measurement"), dict):
            return ref["measurement"]
    metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
    if metadata.get("metric") and metadata.get("value") is not None:
        return {
            "metric_name": metadata.get("metric"),
            "measured_value": metadata.get("value"),
            "threshold": metadata.get("threshold"),
            "threshold_operator": "gt",
            "scope": metadata.get("scope"),
        }
    return None


def _first_evidence_path(evidence: Any) -> str | None:
    if not isinstance(evidence, list):
        return None
    for item in evidence:
        if isinstance(item, dict):
            path = item.get("path") or item.get("file") or item.get("file_path")
            if path:
                return str(path)
    return None


def _as_number(value: Any) -> int | float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number.is_integer():
        return int(number)
    return number


def _parse_metric(value: str | None) -> TechnicalDebtMetric:
    raw = (value or "").strip().lower().removeprefix("measurement.")
    return (
        TechnicalDebtMetric(raw)
        if raw in TechnicalDebtMetric._value2member_map_
        else TechnicalDebtMetric.OTHER
    )


def _parse_scope(value: str | None) -> TechnicalDebtScope:
    raw = (value or "").strip().lower()
    return (
        TechnicalDebtScope(raw)
        if raw in TechnicalDebtScope._value2member_map_
        else TechnicalDebtScope.OTHER
    )


def _looks_non_production_path(path: str) -> bool:
    lowered = path.replace("\\", "/").lower()
    markers = (
        "/test/",
        "/tests/",
        "/__tests__/",
        "/src/test/",
        "/fixtures/",
        "/fixture/",
        "/generated/",
        "/.generated/",
    )
    return any(marker in lowered for marker in markers)


def _is_disclaimer_negation(text: str, claim: str) -> bool:
    patterns = (
        rf"do not certify {re.escape(claim)}",
        rf"does not certify {re.escape(claim)}",
        rf"zero findings do not certify {re.escape(claim)}",
        rf"were not evaluated",
        rf"were not assessed",
        rf"broader technical debt categories were not evaluated",
    )
    return any(re.search(pattern, text) for pattern in patterns)


def _norm(value: str) -> str:
    return value.strip().lower()


def _norm_path(value: str) -> str:
    return value.replace("\\", "/").strip().lstrip("./")
