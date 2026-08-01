"""Architecture precision validation (Epic 4 Slice 4.5).

Evidence-authored Architecture expectations, TP/FP/FN classification, and
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


class ArchitectureCategory(StrEnum):
    DEPENDENCY_STRUCTURE = "dependency_structure"
    DIRECTED_CYCLES = "directed_cycles"
    LAYERING = "layering"
    BOUNDARY = "boundary"
    FAN_OUT = "fan_out"
    COUPLING = "coupling"
    CONCENTRATION = "concentration"
    MODULAR = "modular"
    GRAPH_REFERENCE = "graph_reference"
    SOURCE_LOCATION = "source_location"
    LEGACY = "legacy"
    OTHER = "other"


_RULE_CATEGORY: dict[str, ArchitectureCategory] = {
    "architecture.dependency-cycle": ArchitectureCategory.DIRECTED_CYCLES,
    "architecture.invalid-dependency-direction": ArchitectureCategory.LAYERING,
    "architecture.layer-boundary-violation": ArchitectureCategory.BOUNDARY,
    "architecture.excessive-cross-module-coupling": ArchitectureCategory.COUPLING,
    "architecture.component-concentration": ArchitectureCategory.CONCENTRATION,
    "architecture.framework-leakage": ArchitectureCategory.BOUNDARY,
    "architecture.enterprise-standard-mismatch": ArchitectureCategory.OTHER,
}


class ArchitectureFindingExpectation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    subject: str | None = None
    subject_pattern: str | None = None
    path: str | None = None
    path_pattern: str | None = None
    severity: str | None = None
    confidence: str | None = None
    expected_count: int | None = Field(default=None, ge=0)
    graph_reference_kind: str | None = None
    category: ArchitectureCategory | None = None
    rationale: str = ""


class ArchitectureEdgeExpectation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source: str
    target: str
    rationale: str = ""

    def key(self) -> str:
        return f"{_norm(self.source)}->{_norm(self.target)}"


class ArchitectureCycleExpectation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    nodes: tuple[str, ...]
    rationale: str = ""

    def canonical(self) -> tuple[str, ...]:
        return canonicalize_cycle(self.nodes)


class ArchitectureRuleCountRange(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    minimum: int | None = Field(default=None, ge=0)
    maximum: int | None = Field(default=None, ge=0)
    exact: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _validate_range(self) -> ArchitectureRuleCountRange:
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


class ArchitectureExpectation(BaseModel):
    """Evidence-authored Architecture precision expectations for one repository."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    required_findings: tuple[ArchitectureFindingExpectation, ...] = ()
    forbidden_findings: tuple[ArchitectureFindingExpectation, ...] = ()
    allowed_findings: tuple[ArchitectureFindingExpectation, ...] = ()
    expected_rule_ids: tuple[str, ...] = ()
    forbidden_rule_ids: tuple[str, ...] = ()
    required_nodes: tuple[str, ...] = ()
    required_edges: tuple[ArchitectureEdgeExpectation, ...] = ()
    forbidden_edges: tuple[ArchitectureEdgeExpectation, ...] = ()
    expected_cycles: tuple[ArchitectureCycleExpectation, ...] = ()
    forbidden_cycles: tuple[ArchitectureCycleExpectation, ...] = ()
    expected_rule_count_ranges: tuple[ArchitectureRuleCountRange, ...] = ()
    expected_graph_reference_counts: ArchitectureRuleCountRange | None = None
    maximum_false_positive_count: int | None = Field(default=None, ge=0)
    expected_limitations: tuple[str, ...] = ()
    expected_coverage_state: str | None = None
    not_applicable_rule_ids: tuple[str, ...] = ()
    forbidden_unsupported_claims: tuple[str, ...] = ()
    evidence_notes: str | None = None

    @model_validator(mode="after")
    def _reject_contradictions(self) -> ArchitectureExpectation:
        required_any = {item.rule_id for item in self.required_findings} | set(
            self.expected_rule_ids
        )
        overlap_global = sorted(required_any & set(self.forbidden_rule_ids))
        if overlap_global:
            raise ValueError(
                f"contradictory architecture rule expectations: {overlap_global}"
            )
        required_global = set(self.expected_rule_ids) | {
            item.rule_id
            for item in self.required_findings
            if not item.path
            and not item.path_pattern
            and not item.subject
            and not item.subject_pattern
        }
        forbidden_global = set(self.forbidden_rule_ids) | {
            item.rule_id
            for item in self.forbidden_findings
            if not item.path
            and not item.path_pattern
            and not item.subject
            and not item.subject_pattern
        }
        overlap = sorted(required_global & forbidden_global)
        if overlap:
            raise ValueError(f"contradictory architecture rule expectations: {overlap}")
        req_edges = {item.key() for item in self.required_edges}
        forb_edges = {item.key() for item in self.forbidden_edges}
        edge_overlap = sorted(req_edges & forb_edges)
        if edge_overlap:
            raise ValueError(f"contradictory architecture edge expectations: {edge_overlap}")
        return self


class ArchitectureFindingActual(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    finding_id: str | None = None
    path: str | None = None
    subject: str | None = None
    severity: str | None = None
    confidence: str | None = None
    evidence_ids: tuple[str, ...] = ()
    graph_reference_kinds: tuple[str, ...] = ()
    category: ArchitectureCategory = ArchitectureCategory.OTHER


class ArchitectureGraphActual(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    nodes: tuple[str, ...] = ()
    edges: tuple[str, ...] = ()
    cycles: tuple[tuple[str, ...], ...] = ()
    coverage_state: str | None = None
    graph_fingerprint: str | None = None


class ClassifiedArchitectureFact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    rule_id: str
    classification: FactClassification
    expectation: str
    actual: str
    diagnostic: str
    category: ArchitectureCategory = ArchitectureCategory.OTHER
    path: str | None = None


class ArchitectureRuleMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    category: ArchitectureCategory = ArchitectureCategory.OTHER
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    ambiguous: int = 0
    precision: float | None = None
    recall: float | None = None
    unavailable_reason: str | None = None


class ArchitectureValidationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    repository_id: str
    classifications: tuple[ClassifiedArchitectureFact, ...] = ()
    per_rule_metrics: tuple[ArchitectureRuleMetrics, ...] = ()
    per_category_metrics: tuple[ArchitectureRuleMetrics, ...] = ()
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    ambiguous: int = 0
    precision: float | None = None
    recall: float | None = None
    unsupported_claim_failures: tuple[str, ...] = ()
    graph_failures: tuple[str, ...] = ()
    path_failures: tuple[str, ...] = ()
    passed: bool = True
    diagnostics: tuple[str, ...] = ()


class AggregateArchitectureMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    repository_count: int = 0
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    ambiguous: int = 0
    precision: float | None = None
    recall: float | None = None
    per_rule: tuple[ArchitectureRuleMetrics, ...] = ()
    per_category: tuple[ArchitectureRuleMetrics, ...] = ()
    per_repository: tuple[ArchitectureValidationResult, ...] = ()


def canonicalize_cycle(nodes: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """Rotation-invariant cycle identity (exclude trailing repeat of start)."""

    cleaned = [_norm(item) for item in nodes if item]
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1]:
        cleaned = cleaned[:-1]
    if not cleaned:
        return ()
    rotations = [tuple(cleaned[i:] + cleaned[:i]) for i in range(len(cleaned))]
    return min(rotations)


def category_for_rule(rule_id: str) -> ArchitectureCategory:
    if rule_id in _RULE_CATEGORY:
        return _RULE_CATEGORY[rule_id]
    if rule_id.upper().startswith("ARCH"):
        return ArchitectureCategory.LEGACY
    if rule_id.startswith("architecture."):
        return ArchitectureCategory.OTHER
    return ArchitectureCategory.OTHER


def extract_architecture_findings(
    findings: list[Any] | tuple[Any, ...],
) -> tuple[ArchitectureFindingActual, ...]:
    rows: list[ArchitectureFindingActual] = []
    for item in findings:
        if not isinstance(item, dict):
            continue
        rule_id = str(item.get("rule_id") or "").strip()
        if not rule_id:
            continue
        if not (
            rule_id.startswith("architecture.")
            or rule_id.upper().startswith("ARCH")
        ):
            continue
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        path = (
            metadata.get("path")
            or item.get("path")
            or item.get("file")
            or _first_evidence_path(item.get("evidence"))
        )
        subject = None
        subjects = metadata.get("subject_keys")
        if isinstance(subjects, (list, tuple)) and subjects:
            subject = ",".join(str(part) for part in subjects)
        elif metadata.get("subject"):
            subject = str(metadata["subject"])
        evidence_ids: list[str] = []
        graph_kinds: list[str] = []
        for ref in item.get("evidence_refs") or []:
            if isinstance(ref, dict):
                eid = ref.get("evidence_id") or ref.get("id")
                if eid:
                    evidence_ids.append(str(eid))
                graph = ref.get("graph_ref") if isinstance(ref.get("graph_ref"), dict) else {}
                kind = graph.get("kind") or graph.get("reference_kind")
                if kind:
                    graph_kinds.append(str(kind))
        for evidence in item.get("evidence") or []:
            if isinstance(evidence, dict):
                eid = evidence.get("source_id") or evidence.get("evidence_id") or evidence.get("id")
                if eid:
                    evidence_ids.append(str(eid))
        if item.get("primary_evidence_id"):
            evidence_ids.append(str(item["primary_evidence_id"]))
        rows.append(
            ArchitectureFindingActual(
                rule_id=rule_id,
                finding_id=str(item.get("id")) if item.get("id") else None,
                path=str(path) if path else None,
                subject=subject,
                severity=str(item.get("severity")).lower() if item.get("severity") else None,
                confidence=(
                    str(metadata.get("confidence") or item.get("confidence")).lower()
                    if (metadata.get("confidence") or item.get("confidence"))
                    else None
                ),
                evidence_ids=tuple(sorted(set(evidence_ids))),
                graph_reference_kinds=tuple(sorted(set(graph_kinds))),
                category=category_for_rule(rule_id),
            )
        )
    return tuple(rows)


def extract_architecture_graph(document: dict[str, Any]) -> ArchitectureGraphActual:
    """Extract lightweight architecture graph facts from report payloads."""

    assessment = document.get("assessment") if isinstance(document.get("assessment"), dict) else {}
    architecture = (
        assessment.get("architecture") if isinstance(assessment.get("architecture"), dict) else {}
    )
    nodes: set[str] = set()
    edges: set[str] = set()
    cycles: list[tuple[str, ...]] = []

    trace = (
        architecture.get("traceability_summary")
        if isinstance(architecture.get("traceability_summary"), dict)
        else {}
    )
    for sample in trace.get("sample_edges") or []:
        if isinstance(sample, dict):
            source = sample.get("source") or sample.get("from") or sample.get("source_id")
            target = sample.get("target") or sample.get("to") or sample.get("target_id")
            if source and target:
                edges.add(f"{_norm(str(source))}->{_norm(str(target))}")
                nodes.add(_norm(str(source)))
                nodes.add(_norm(str(target)))
        elif isinstance(sample, str) and "->" in sample:
            edges.add(_norm_edge(sample))
            left, right = sample.split("->", 1)
            nodes.add(_norm(left))
            nodes.add(_norm(right))

    for key in ("nodes", "units", "module_ids"):
        for item in architecture.get(key) or []:
            if isinstance(item, str):
                nodes.add(_norm(item))
            elif isinstance(item, dict):
                uid = item.get("id") or item.get("unit_id") or item.get("name")
                if uid:
                    nodes.add(_norm(str(uid)))

    coverage = architecture.get("coverage_summary") or architecture.get("status")
    coverage_state = None
    if isinstance(coverage, dict):
        coverage_state = str(
            coverage.get("state") or coverage.get("status") or coverage.get("coverage_state") or ""
        ) or None
    elif isinstance(coverage, str):
        coverage_state = coverage

    fingerprint = None
    meta = architecture.get("metadata") if isinstance(architecture.get("metadata"), dict) else {}
    if meta.get("graph_fingerprint"):
        fingerprint = str(meta["graph_fingerprint"])

    return ArchitectureGraphActual(
        nodes=tuple(sorted(nodes)),
        edges=tuple(sorted(edges)),
        cycles=tuple(cycles),
        coverage_state=coverage_state,
        graph_fingerprint=fingerprint,
    )


def validate_architecture_precision(
    *,
    repository_id: str,
    expectation: ArchitectureExpectation,
    actual_findings: tuple[ArchitectureFindingActual, ...] | list[ArchitectureFindingActual],
    graph: ArchitectureGraphActual | None = None,
    artifact_texts: dict[str, str] | None = None,
) -> ArchitectureValidationResult:
    actual = tuple(actual_findings)
    graph = graph or ArchitectureGraphActual()
    classifications: list[ClassifiedArchitectureFact] = []
    allowed_rule_ids = {item.rule_id for item in expectation.allowed_findings}
    na_rules = {_norm(item) for item in expectation.not_applicable_rule_ids}
    structured_required = {item.rule_id for item in expectation.required_findings}

    for req in expectation.required_findings:
        matches = [item for item in actual if _finding_matches(req, item)]
        expected_count = req.expected_count if req.expected_count is not None else 1
        category = req.category or category_for_rule(req.rule_id)
        if len(matches) >= expected_count:
            classifications.append(
                ClassifiedArchitectureFact(
                    name=req.rule_id,
                    rule_id=req.rule_id,
                    classification=FactClassification.TRUE_POSITIVE,
                    expectation=_expect_text(req),
                    actual=f"count={len(matches)}",
                    diagnostic=req.rationale or "required architecture finding matched",
                    category=category,
                    path=req.path,
                )
            )
        else:
            classifications.append(
                ClassifiedArchitectureFact(
                    name=req.rule_id,
                    rule_id=req.rule_id,
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=_expect_text(req),
                    actual=f"count={len(matches)}",
                    diagnostic=req.rationale or "required architecture finding missing",
                    category=category,
                    path=req.path,
                )
            )

    for rule_id in expectation.expected_rule_ids:
        if rule_id in structured_required:
            continue
        if _norm(rule_id) in na_rules:
            classifications.append(
                ClassifiedArchitectureFact(
                    name=rule_id,
                    rule_id=rule_id,
                    classification=FactClassification.NOT_APPLICABLE,
                    expectation="not applicable",
                    actual="skipped",
                    diagnostic="rule marked not_applicable",
                    category=category_for_rule(rule_id),
                )
            )
            continue
        present = [item for item in actual if item.rule_id == rule_id]
        if present:
            classifications.append(
                ClassifiedArchitectureFact(
                    name=rule_id,
                    rule_id=rule_id,
                    classification=FactClassification.TRUE_POSITIVE,
                    expectation=f"required rule {rule_id}",
                    actual=f"count={len(present)}",
                    diagnostic="required rule present",
                    category=category_for_rule(rule_id),
                )
            )
        else:
            classifications.append(
                ClassifiedArchitectureFact(
                    name=rule_id,
                    rule_id=rule_id,
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=f"required rule {rule_id}",
                    actual="absent",
                    diagnostic="required rule missing",
                    category=category_for_rule(rule_id),
                )
            )

    for forb in expectation.forbidden_findings:
        matches = [item for item in actual if _finding_matches(forb, item)]
        for match in matches:
            classifications.append(
                ClassifiedArchitectureFact(
                    name=forb.rule_id,
                    rule_id=forb.rule_id,
                    classification=FactClassification.FALSE_POSITIVE,
                    expectation=_expect_text(forb),
                    actual=f"path={match.path!r} subject={match.subject!r}",
                    diagnostic=forb.rationale or "forbidden architecture finding present",
                    category=forb.category or category_for_rule(forb.rule_id),
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
                    ClassifiedArchitectureFact(
                        name=rule_id,
                        rule_id=rule_id,
                        classification=FactClassification.AMBIGUOUS,
                        expectation="allowed overlap",
                        actual=f"path={match.path!r}",
                        diagnostic="allowed finding excluded from FP scoring",
                        category=category_for_rule(rule_id),
                        path=match.path,
                    )
                )
            else:
                classifications.append(
                    ClassifiedArchitectureFact(
                        name=rule_id,
                        rule_id=rule_id,
                        classification=FactClassification.FALSE_POSITIVE,
                        expectation=f"forbidden rule {rule_id}",
                        actual=f"path={match.path!r}",
                        diagnostic="forbidden rule present",
                        category=category_for_rule(rule_id),
                        path=match.path,
                    )
                )

    for allowed in expectation.allowed_findings:
        matches = [item for item in actual if _finding_matches(allowed, item)]
        if matches and allowed.rule_id not in structured_required:
            classifications.append(
                ClassifiedArchitectureFact(
                    name=allowed.rule_id,
                    rule_id=allowed.rule_id,
                    classification=FactClassification.AMBIGUOUS,
                    expectation=allowed.rationale or "allowed finding",
                    actual=f"count={len(matches)}",
                    diagnostic="allowed finding not scored as TP",
                    category=allowed.category or category_for_rule(allowed.rule_id),
                    path=allowed.path,
                )
            )

    for range_spec in expectation.expected_rule_count_ranges:
        count = sum(1 for item in actual if item.rule_id == range_spec.rule_id)
        if not range_spec.contains(count):
            classifications.append(
                ClassifiedArchitectureFact(
                    name=range_spec.rule_id,
                    rule_id=range_spec.rule_id,
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=f"count {range_spec.describe()}",
                    actual=f"count={count}",
                    diagnostic="rule count outside range",
                    category=category_for_rule(range_spec.rule_id),
                )
            )

    graph_failures: list[str] = []
    for node in expectation.required_nodes:
        if _norm(node) not in {_norm(item) for item in graph.nodes}:
            # Soft graph facts: missing sample nodes are FN only when graph has any nodes.
            if graph.nodes:
                classifications.append(
                    ClassifiedArchitectureFact(
                        name=node,
                        rule_id="architecture.graph-node",
                        classification=FactClassification.FALSE_NEGATIVE,
                        expectation=f"required node {node}",
                        actual="absent",
                        diagnostic="required architecture node missing from report graph sample",
                        category=ArchitectureCategory.GRAPH_REFERENCE,
                    )
                )
            else:
                graph_failures.append(f"required_node_unavailable:{node}")

    actual_edges = {_norm_edge(item) for item in graph.edges}
    for edge in expectation.required_edges:
        if edge.key() not in actual_edges:
            if graph.edges:
                classifications.append(
                    ClassifiedArchitectureFact(
                        name=edge.key(),
                        rule_id="architecture.graph-edge",
                        classification=FactClassification.FALSE_NEGATIVE,
                        expectation=f"required edge {edge.key()}",
                        actual="absent",
                        diagnostic=edge.rationale or "required edge missing",
                        category=ArchitectureCategory.DEPENDENCY_STRUCTURE,
                    )
                )
            else:
                graph_failures.append(f"required_edge_unavailable:{edge.key()}")
    for edge in expectation.forbidden_edges:
        if edge.key() in actual_edges:
            classifications.append(
                ClassifiedArchitectureFact(
                    name=edge.key(),
                    rule_id="architecture.graph-edge",
                    classification=FactClassification.FALSE_POSITIVE,
                    expectation=f"forbidden edge {edge.key()}",
                    actual="present",
                    diagnostic=edge.rationale or "forbidden edge present",
                    category=ArchitectureCategory.DEPENDENCY_STRUCTURE,
                )
            )

    actual_cycles = {canonicalize_cycle(item) for item in graph.cycles}
    for cycle in expectation.expected_cycles:
        if cycle.canonical() not in actual_cycles:
            classifications.append(
                ClassifiedArchitectureFact(
                    name="->".join(cycle.canonical()),
                    rule_id="architecture.dependency-cycle",
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=f"expected cycle {cycle.canonical()}",
                    actual="absent",
                    diagnostic=cycle.rationale or "expected cycle missing",
                    category=ArchitectureCategory.DIRECTED_CYCLES,
                )
            )
    for cycle in expectation.forbidden_cycles:
        if cycle.canonical() in actual_cycles:
            classifications.append(
                ClassifiedArchitectureFact(
                    name="->".join(cycle.canonical()),
                    rule_id="architecture.dependency-cycle",
                    classification=FactClassification.FALSE_POSITIVE,
                    expectation=f"forbidden cycle {cycle.canonical()}",
                    actual="present",
                    diagnostic=cycle.rationale or "forbidden invented cycle",
                    category=ArchitectureCategory.DIRECTED_CYCLES,
                )
            )

    if expectation.expected_coverage_state and graph.coverage_state:
        if _norm(expectation.expected_coverage_state) != _norm(graph.coverage_state):
            classifications.append(
                ClassifiedArchitectureFact(
                    name="coverage",
                    rule_id="architecture.coverage",
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=expectation.expected_coverage_state,
                    actual=str(graph.coverage_state),
                    diagnostic="coverage state mismatch",
                    category=ArchitectureCategory.OTHER,
                )
            )

    path_failures: list[str] = []
    for item in actual:
        if item.path and (item.path.startswith("/") or item.path.startswith("\\")):
            path_failures.append(f"absolute_path:{item.rule_id}:{item.path}")
        if item.rule_id.startswith("architecture.") and not item.evidence_ids:
            # Traceability defect for shared-rule findings without evidence linkage.
            path_failures.append(f"missing_evidence:{item.rule_id}:{item.finding_id}")

    if expectation.expected_graph_reference_counts is not None:
        ref_count = sum(1 for item in actual if item.graph_reference_kinds)
        if not expectation.expected_graph_reference_counts.contains(ref_count):
            classifications.append(
                ClassifiedArchitectureFact(
                    name="graph_refs",
                    rule_id="architecture.graph-reference",
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=expectation.expected_graph_reference_counts.describe(),
                    actual=f"count={ref_count}",
                    diagnostic="graph reference count outside range",
                    category=ArchitectureCategory.GRAPH_REFERENCE,
                )
            )

    unsupported: list[str] = []
    artifact_texts = artifact_texts or {}
    for claim in expectation.forbidden_unsupported_claims:
        needle = claim.lower()
        for name, text in artifact_texts.items():
            # Allow explicit disclaimer phrasing that negates the claim.
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
    per_category = _per_category_metrics(classifications)
    diagnostics = [
        f"{item.classification.value}:{item.rule_id}:{item.diagnostic}"
        for item in classifications
        if item.classification
        in {FactClassification.FALSE_POSITIVE, FactClassification.FALSE_NEGATIVE}
    ]
    diagnostics.extend(f"unsupported:{item}" for item in unsupported)
    diagnostics.extend(f"graph:{item}" for item in graph_failures)
    diagnostics.extend(f"path:{item}" for item in path_failures)

    passed = fp == 0 and fn == 0 and not unsupported and not path_failures
    if expectation.maximum_false_positive_count is not None:
        passed = passed and fp <= expectation.maximum_false_positive_count

    return ArchitectureValidationResult(
        repository_id=repository_id,
        classifications=tuple(classifications),
        per_rule_metrics=per_rule,
        per_category_metrics=per_category,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        ambiguous=amb,
        precision=precision,
        recall=recall,
        unsupported_claim_failures=tuple(unsupported),
        graph_failures=tuple(graph_failures),
        path_failures=tuple(path_failures),
        passed=passed,
        diagnostics=tuple(diagnostics),
    )


def aggregate_architecture_results(
    results: list[ArchitectureValidationResult] | tuple[ArchitectureValidationResult, ...],
) -> AggregateArchitectureMetrics:
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
    by_category: dict[str, list[int]] = {}
    for result in results_t:
        for metrics in result.per_rule_metrics:
            bucket = by_rule.setdefault(metrics.rule_id, [0, 0, 0, 0, metrics.category])
            bucket[0] += metrics.true_positives
            bucket[1] += metrics.false_positives
            bucket[2] += metrics.false_negatives
            bucket[3] += metrics.ambiguous
        for metrics in result.per_category_metrics:
            bucket = by_category.setdefault(metrics.rule_id, [0, 0, 0, 0])
            bucket[0] += metrics.true_positives
            bucket[1] += metrics.false_positives
            bucket[2] += metrics.false_negatives
            bucket[3] += metrics.ambiguous
    per_rule: list[ArchitectureRuleMetrics] = []
    for rule_id, (rtp, rfp, rfn, ramb, category) in sorted(by_rule.items()):
        rprec, rrec, rreason = compute_precision_recall(
            true_positives=rtp,
            false_positives=rfp,
            false_negatives=rfn,
        )
        per_rule.append(
            ArchitectureRuleMetrics(
                rule_id=rule_id,
                category=category,
                true_positives=rtp,
                false_positives=rfp,
                false_negatives=rfn,
                ambiguous=ramb,
                precision=rprec,
                recall=rrec,
                unavailable_reason=rreason,
            )
        )
    per_category: list[ArchitectureRuleMetrics] = []
    for category, (ctp, cfp, cfn, camb) in sorted(by_category.items()):
        cprec, crec, creason = compute_precision_recall(
            true_positives=ctp,
            false_positives=cfp,
            false_negatives=cfn,
        )
        per_category.append(
            ArchitectureRuleMetrics(
                rule_id=category,
                category=ArchitectureCategory(category)
                if category in ArchitectureCategory._value2member_map_
                else ArchitectureCategory.OTHER,
                true_positives=ctp,
                false_positives=cfp,
                false_negatives=cfn,
                ambiguous=camb,
                precision=cprec,
                recall=crec,
                unavailable_reason=creason,
            )
        )
    return AggregateArchitectureMetrics(
        repository_count=len(results_t),
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        ambiguous=amb,
        precision=precision,
        recall=recall,
        per_rule=tuple(per_rule),
        per_category=tuple(per_category),
        per_repository=results_t,
    )


def _finding_matches(
    expectation: ArchitectureFindingExpectation,
    actual: ArchitectureFindingActual,
) -> bool:
    if actual.rule_id != expectation.rule_id:
        return False
    if expectation.path and _norm_path(actual.path or "") != _norm_path(expectation.path):
        return False
    if expectation.path_pattern:
        if not actual.path or not re.search(expectation.path_pattern, actual.path):
            return False
    if expectation.subject and _norm(actual.subject or "") != _norm(expectation.subject):
        return False
    if expectation.subject_pattern:
        if not actual.subject or not re.search(expectation.subject_pattern, actual.subject):
            return False
    if expectation.severity and _norm(actual.severity or "") != _norm(expectation.severity):
        return False
    if expectation.graph_reference_kind:
        if expectation.graph_reference_kind not in actual.graph_reference_kinds:
            return False
    return True


def _expect_text(item: ArchitectureFindingExpectation) -> str:
    parts = [f"rule={item.rule_id}"]
    if item.path:
        parts.append(f"path={item.path}")
    if item.path_pattern:
        parts.append(f"path_pattern={item.path_pattern}")
    if item.subject:
        parts.append(f"subject={item.subject}")
    if item.expected_count is not None:
        parts.append(f"count={item.expected_count}")
    return ",".join(parts)


def _per_rule_metrics(
    classifications: list[ClassifiedArchitectureFact],
) -> tuple[ArchitectureRuleMetrics, ...]:
    rules = sorted({item.rule_id for item in classifications})
    metrics: list[ArchitectureRuleMetrics] = []
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
            ArchitectureRuleMetrics(
                rule_id=rule_id,
                category=scoped[0].category if scoped else category_for_rule(rule_id),
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


def _per_category_metrics(
    classifications: list[ClassifiedArchitectureFact],
) -> tuple[ArchitectureRuleMetrics, ...]:
    categories = sorted({item.category.value for item in classifications})
    metrics: list[ArchitectureRuleMetrics] = []
    for category in categories:
        scoped = [item for item in classifications if item.category.value == category]
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
            ArchitectureRuleMetrics(
                rule_id=category,
                category=ArchitectureCategory(category),
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


def _is_disclaimer_negation(text: str, claim: str) -> bool:
    """Treat negated disclaimer phrases as safe (not unsupported claims)."""

    patterns = (
        rf"do not certify {re.escape(claim)}",
        rf"does not certify {re.escape(claim)}",
        rf"zero findings do not certify {re.escape(claim)}",
        rf"not assess(ed)? .*{re.escape(claim)}",
        rf"were not assessed",
    )
    return any(re.search(pattern, text) for pattern in patterns)


def _norm(value: str) -> str:
    return value.strip().lower()


def _norm_path(value: str) -> str:
    return value.replace("\\", "/").strip().lstrip("./")


def _norm_edge(value: str) -> str:
    if "->" not in value:
        return _norm(value)
    left, right = value.split("->", 1)
    return f"{_norm(left)}->{_norm(right)}"
