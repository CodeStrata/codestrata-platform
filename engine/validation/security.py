"""Security precision validation (Epic 4 Slice 4.4).

Evidence-authored Security expectations, TP/FP/FN classification, and
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


class SecurityRuleFamily(StrEnum):
    PRIVATE_KEY = "security.private-key-material"
    CREDENTIAL_LITERAL = "security.credential-literal"
    PLACEHOLDER = "security.placeholder-credential"
    TLS = "security.tls-verification-disabled"
    HOSTNAME = "security.hostname-verification-disabled"
    AUTH = "security.authentication-disabled"
    CORS = "security.permissive-cors-origin"
    DEBUG = "security.debug-enabled"


class SecurityFindingExpectation(BaseModel):
    """One required, forbidden, or allowed Security finding expectation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    path: str | None = None
    path_pattern: str | None = None
    context: str | None = None
    severity: str | None = None
    confidence: str | None = None
    expected_count: int | None = Field(default=None, ge=0)
    evidence_kind: str | None = None
    redaction_required: bool = True
    rationale: str = ""


class SecurityRuleCountRange(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    minimum: int | None = Field(default=None, ge=0)
    maximum: int | None = Field(default=None, ge=0)
    exact: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _validate_range(self) -> SecurityRuleCountRange:
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


class SecurityExpectation(BaseModel):
    """Evidence-authored Security precision expectations for one repository."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    required_findings: tuple[SecurityFindingExpectation, ...] = ()
    forbidden_findings: tuple[SecurityFindingExpectation, ...] = ()
    allowed_findings: tuple[SecurityFindingExpectation, ...] = ()
    expected_rule_ids: tuple[str, ...] = ()
    forbidden_rule_ids: tuple[str, ...] = ()
    expected_rule_count_ranges: tuple[SecurityRuleCountRange, ...] = ()
    maximum_false_positive_count: int | None = Field(default=None, ge=0)
    expected_limitations: tuple[str, ...] = ()
    forbidden_raw_values: tuple[str, ...] = ()
    expected_contexts: tuple[str, ...] = ()
    forbidden_contexts_for_production_risk: tuple[str, ...] = ()
    not_applicable_rule_ids: tuple[str, ...] = ()
    evidence_notes: str | None = None

    @model_validator(mode="after")
    def _reject_contradictions(self) -> SecurityExpectation:
        # Global required vs global forbidden rule IDs only.
        # Path-scoped forbidden_findings may share a rule_id with required
        # findings (e.g. credential-literal required on config/, forbidden on CI).
        required_global = set(self.expected_rule_ids) | {
            item.rule_id
            for item in self.required_findings
            if not item.path and not item.path_pattern
        }
        forbidden_global = set(self.forbidden_rule_ids) | {
            item.rule_id
            for item in self.forbidden_findings
            if not item.path and not item.path_pattern
        }
        overlap = sorted(required_global & forbidden_global)
        if overlap:
            raise ValueError(f"contradictory security rule expectations: {overlap}")
        # Also reject when the same rule is required (any) and globally forbidden.
        required_any = {item.rule_id for item in self.required_findings} | set(
            self.expected_rule_ids
        )
        overlap_global_forbid = sorted(required_any & set(self.forbidden_rule_ids))
        if overlap_global_forbid:
            raise ValueError(
                f"contradictory security rule expectations: {overlap_global_forbid}"
            )
        return self


class SecurityFindingActual(BaseModel):
    """Normalized Security finding extracted from report.json."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    finding_id: str | None = None
    path: str | None = None
    context: str | None = None
    severity: str | None = None
    confidence: str | None = None
    redacted_preview: str | None = None
    evidence_ids: tuple[str, ...] = ()


class ClassifiedSecurityFact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    rule_id: str
    classification: FactClassification
    expectation: str
    actual: str
    diagnostic: str
    path: str | None = None


class SecurityRuleMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    ambiguous: int = 0
    precision: float | None = None
    recall: float | None = None
    unavailable_reason: str | None = None


class SecurityValidationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    repository_id: str
    classifications: tuple[ClassifiedSecurityFact, ...] = ()
    per_rule_metrics: tuple[SecurityRuleMetrics, ...] = ()
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    ambiguous: int = 0
    precision: float | None = None
    recall: float | None = None
    redaction_failures: tuple[str, ...] = ()
    production_context_errors: tuple[str, ...] = ()
    passed: bool = True
    diagnostics: tuple[str, ...] = ()


class AggregateSecurityMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    repository_count: int = 0
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    ambiguous: int = 0
    precision: float | None = None
    recall: float | None = None
    per_rule: tuple[SecurityRuleMetrics, ...] = ()
    per_repository: tuple[SecurityValidationResult, ...] = ()


def extract_security_findings(findings: list[Any] | tuple[Any, ...]) -> tuple[SecurityFindingActual, ...]:
    """Normalize customer findings into SecurityFindingActual rows."""

    rows: list[SecurityFindingActual] = []
    for item in findings:
        if not isinstance(item, dict):
            continue
        rule_id = str(item.get("rule_id") or "").strip()
        if not rule_id:
            continue
        # Include SharedRule security.* and legacy SEC* analyzer findings.
        if not (
            rule_id.startswith("security.")
            or rule_id.upper().startswith("SEC")
        ):
            continue
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        path = (
            metadata.get("path")
            or item.get("path")
            or item.get("file")
            or _first_evidence_path(item.get("evidence"))
        )
        context = metadata.get("security_context") or item.get("security_context")
        evidence_ids: list[str] = []
        for evidence in item.get("evidence") or []:
            if isinstance(evidence, dict):
                eid = evidence.get("source_id") or evidence.get("evidence_id") or evidence.get("id")
                if eid:
                    evidence_ids.append(str(eid))
        if metadata.get("evidence_id"):
            evidence_ids.append(str(metadata["evidence_id"]))
        rows.append(
            SecurityFindingActual(
                rule_id=rule_id,
                finding_id=str(item.get("id")) if item.get("id") else None,
                path=str(path) if path else None,
                context=str(context) if context else None,
                severity=str(item.get("severity")).lower() if item.get("severity") else None,
                confidence=(
                    str(metadata.get("confidence") or item.get("confidence")).lower()
                    if (metadata.get("confidence") or item.get("confidence"))
                    else None
                ),
                redacted_preview=(
                    str(metadata["redacted_preview"])
                    if metadata.get("redacted_preview") is not None
                    else None
                ),
                evidence_ids=tuple(sorted(set(evidence_ids))),
            )
        )
    return tuple(rows)


def validate_security_precision(
    *,
    repository_id: str,
    expectation: SecurityExpectation,
    actual_findings: tuple[SecurityFindingActual, ...] | list[SecurityFindingActual],
    artifact_texts: dict[str, str] | None = None,
) -> SecurityValidationResult:
    """Compare evidence-backed Security expectations to normalized findings."""

    actual = tuple(actual_findings)
    classifications: list[ClassifiedSecurityFact] = []
    allowed_rule_ids = {item.rule_id for item in expectation.allowed_findings}
    na_rules = {_norm(item) for item in expectation.not_applicable_rule_ids}

    # Required findings (structured)
    for req in expectation.required_findings:
        matches = [item for item in actual if _finding_matches(req, item)]
        expected_count = req.expected_count if req.expected_count is not None else 1
        if len(matches) >= expected_count:
            classifications.append(
                ClassifiedSecurityFact(
                    name=req.rule_id,
                    rule_id=req.rule_id,
                    classification=FactClassification.TRUE_POSITIVE,
                    expectation=_expect_text(req),
                    actual=f"count={len(matches)}",
                    diagnostic=req.rationale or "required security finding matched",
                    path=req.path,
                )
            )
        else:
            classifications.append(
                ClassifiedSecurityFact(
                    name=req.rule_id,
                    rule_id=req.rule_id,
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=_expect_text(req),
                    actual=f"count={len(matches)}",
                    diagnostic=req.rationale or "required security finding missing",
                    path=req.path,
                )
            )

    # Shorthand required rule IDs
    structured_required = {item.rule_id for item in expectation.required_findings}
    for rule_id in expectation.expected_rule_ids:
        if rule_id in structured_required:
            continue
        if _norm(rule_id) in na_rules:
            classifications.append(
                ClassifiedSecurityFact(
                    name=rule_id,
                    rule_id=rule_id,
                    classification=FactClassification.NOT_APPLICABLE,
                    expectation="not applicable",
                    actual="skipped",
                    diagnostic="rule marked not_applicable",
                )
            )
            continue
        present = [item for item in actual if item.rule_id == rule_id]
        if present:
            classifications.append(
                ClassifiedSecurityFact(
                    name=rule_id,
                    rule_id=rule_id,
                    classification=FactClassification.TRUE_POSITIVE,
                    expectation=f"required rule {rule_id}",
                    actual=f"count={len(present)}",
                    diagnostic="required rule present",
                )
            )
        else:
            classifications.append(
                ClassifiedSecurityFact(
                    name=rule_id,
                    rule_id=rule_id,
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=f"required rule {rule_id}",
                    actual="absent",
                    diagnostic="required rule missing",
                )
            )

    # Forbidden findings
    for forb in expectation.forbidden_findings:
        matches = [item for item in actual if _finding_matches(forb, item)]
        if matches:
            for match in matches:
                classifications.append(
                    ClassifiedSecurityFact(
                        name=forb.rule_id,
                        rule_id=forb.rule_id,
                        classification=FactClassification.FALSE_POSITIVE,
                        expectation=_expect_text(forb),
                        actual=f"path={match.path!r} context={match.context!r}",
                        diagnostic=forb.rationale or "forbidden security finding present",
                        path=match.path,
                    )
                )

    for rule_id in expectation.forbidden_rule_ids:
        if any(item.rule_id == rule_id for item in expectation.forbidden_findings):
            continue
        matches = [item for item in actual if item.rule_id == rule_id]
        for match in matches:
            if match.rule_id in allowed_rule_ids:
                classifications.append(
                    ClassifiedSecurityFact(
                        name=rule_id,
                        rule_id=rule_id,
                        classification=FactClassification.AMBIGUOUS,
                        expectation="allowed overlap",
                        actual=f"path={match.path!r}",
                        diagnostic="allowed finding excluded from FP scoring",
                        path=match.path,
                    )
                )
            else:
                classifications.append(
                    ClassifiedSecurityFact(
                        name=rule_id,
                        rule_id=rule_id,
                        classification=FactClassification.FALSE_POSITIVE,
                        expectation=f"forbidden rule {rule_id}",
                        actual=f"path={match.path!r}",
                        diagnostic="forbidden rule present",
                        path=match.path,
                    )
                )

    # Allowed findings that appear → ambiguous (not TP unless also required)
    for allowed in expectation.allowed_findings:
        matches = [item for item in actual if _finding_matches(allowed, item)]
        if matches and allowed.rule_id not in structured_required:
            classifications.append(
                ClassifiedSecurityFact(
                    name=allowed.rule_id,
                    rule_id=allowed.rule_id,
                    classification=FactClassification.AMBIGUOUS,
                    expectation=allowed.rationale or "allowed finding",
                    actual=f"count={len(matches)}",
                    diagnostic="allowed finding not scored as TP",
                    path=allowed.path,
                )
            )

    # Count ranges — corroborating checks; success does not inflate TP.
    for range_spec in expectation.expected_rule_count_ranges:
        count = sum(1 for item in actual if item.rule_id == range_spec.rule_id)
        if not range_spec.contains(count):
            classifications.append(
                ClassifiedSecurityFact(
                    name=range_spec.rule_id,
                    rule_id=range_spec.rule_id,
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=f"count {range_spec.describe()}",
                    actual=f"count={count}",
                    diagnostic="rule count outside range",
                )
            )

    # Production-context errors: non-production paths marked as production risk.
    production_errors: list[str] = []
    context_exempt = expectation.allowed_findings + expectation.forbidden_findings
    for item in actual:
        ctx = _norm(item.context or "")
        if item.path and _looks_non_production_path(item.path) and ctx in {"production", "prod"}:
            if any(_finding_matches(exempt, item) for exempt in context_exempt):
                continue
            production_errors.append(f"{item.rule_id}@{item.path}: context={item.context}")

    # Redaction failures
    redaction_failures: list[str] = []
    artifact_texts = artifact_texts or {}
    for raw in expectation.forbidden_raw_values:
        if not raw:
            continue
        for artifact_name, text in artifact_texts.items():
            if raw in text:
                redaction_failures.append(f"{artifact_name}: raw value leaked")

    for item in actual:
        preview = item.redacted_preview or ""
        for raw in expectation.forbidden_raw_values:
            if raw and raw in preview:
                redaction_failures.append(
                    f"{item.rule_id}: redacted_preview contains raw fixture value"
                )

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
    diagnostics = [
        f"{item.classification.value}:{item.rule_id}:{item.diagnostic}"
        for item in classifications
        if item.classification
        in {FactClassification.FALSE_POSITIVE, FactClassification.FALSE_NEGATIVE}
    ]
    diagnostics.extend(f"redaction:{item}" for item in redaction_failures)
    diagnostics.extend(f"context:{item}" for item in production_errors)

    passed = fp == 0 and fn == 0 and not redaction_failures and not production_errors
    if expectation.maximum_false_positive_count is not None:
        passed = passed and fp <= expectation.maximum_false_positive_count

    return SecurityValidationResult(
        repository_id=repository_id,
        classifications=tuple(classifications),
        per_rule_metrics=per_rule,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        ambiguous=amb,
        precision=precision,
        recall=recall,
        redaction_failures=tuple(redaction_failures),
        production_context_errors=tuple(production_errors),
        passed=passed,
        diagnostics=tuple(diagnostics),
    )


def aggregate_security_results(
    results: list[SecurityValidationResult] | tuple[SecurityValidationResult, ...],
) -> AggregateSecurityMetrics:
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
    by_rule: dict[str, list[int]] = {}
    for result in results_t:
        for metrics in result.per_rule_metrics:
            bucket = by_rule.setdefault(metrics.rule_id, [0, 0, 0, 0])
            bucket[0] += metrics.true_positives
            bucket[1] += metrics.false_positives
            bucket[2] += metrics.false_negatives
            bucket[3] += metrics.ambiguous
    per_rule: list[SecurityRuleMetrics] = []
    for rule_id, (rtp, rfp, rfn, ramb) in sorted(by_rule.items()):
        rprec, rrec, rreason = compute_precision_recall(
            true_positives=rtp,
            false_positives=rfp,
            false_negatives=rfn,
        )
        per_rule.append(
            SecurityRuleMetrics(
                rule_id=rule_id,
                true_positives=rtp,
                false_positives=rfp,
                false_negatives=rfn,
                ambiguous=ramb,
                precision=rprec,
                recall=rrec,
                unavailable_reason=rreason,
            )
        )
    return AggregateSecurityMetrics(
        repository_count=len(results_t),
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        ambiguous=amb,
        precision=precision,
        recall=recall,
        per_rule=tuple(per_rule),
        per_repository=results_t,
    )


def _finding_matches(
    expectation: SecurityFindingExpectation,
    actual: SecurityFindingActual,
) -> bool:
    if actual.rule_id != expectation.rule_id:
        return False
    if expectation.path and _norm_path(actual.path or "") != _norm_path(expectation.path):
        return False
    if expectation.path_pattern:
        if not actual.path or not re.search(expectation.path_pattern, actual.path):
            return False
    if expectation.context and _norm(actual.context or "") != _norm(expectation.context):
        return False
    if expectation.severity and _norm(actual.severity or "") != _norm(expectation.severity):
        return False
    return True


def _expect_text(item: SecurityFindingExpectation) -> str:
    parts = [f"rule={item.rule_id}"]
    if item.path:
        parts.append(f"path={item.path}")
    if item.path_pattern:
        parts.append(f"path_pattern={item.path_pattern}")
    if item.context:
        parts.append(f"context={item.context}")
    if item.expected_count is not None:
        parts.append(f"count={item.expected_count}")
    return ",".join(parts)


def _per_rule_metrics(
    classifications: list[ClassifiedSecurityFact],
) -> tuple[SecurityRuleMetrics, ...]:
    rules = sorted({item.rule_id for item in classifications})
    metrics: list[SecurityRuleMetrics] = []
    for rule_id in rules:
        scoped = [item for item in classifications if item.rule_id == rule_id]
        tp = sum(1 for item in scoped if item.classification is FactClassification.TRUE_POSITIVE)
        fp = sum(1 for item in scoped if item.classification is FactClassification.FALSE_POSITIVE)
        fn = sum(1 for item in scoped if item.classification is FactClassification.FALSE_NEGATIVE)
        amb = sum(1 for item in scoped if item.classification is FactClassification.AMBIGUOUS)
        precision, recall, reason = compute_precision_recall(
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
        )
        metrics.append(
            SecurityRuleMetrics(
                rule_id=rule_id,
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


def _first_evidence_path(evidence: Any) -> str | None:
    if not isinstance(evidence, list):
        return None
    for item in evidence:
        if isinstance(item, dict):
            path = item.get("path") or item.get("file") or item.get("file_path")
            if path:
                return str(path)
    return None


def _looks_non_production_path(path: str) -> bool:
    """Paths that must not be presented as production risk.

    Intentional controlled positives under ``secrets/`` or ``config/`` may use
    TEST_ONLY filenames without implying test-context classification.
    """

    lowered = path.replace("\\", "/").lower()
    markers = (
        "/test/",
        "/tests/",
        "/fixture/",
        "/fixtures/",
        "/docs/",
        "/documentation/",
        "/examples/",
        "readme.md",
        ".github/workflows/",
    )
    return any(marker in lowered for marker in markers)


def _norm(value: str) -> str:
    return value.strip().lower()


def _norm_path(value: str) -> str:
    return value.replace("\\", "/").strip().lstrip("./")
