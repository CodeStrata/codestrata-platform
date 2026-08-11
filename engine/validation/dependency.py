"""Dependency precision validation (Epic 4 Slice 4.7).

Evidence-authored Dependency declaration-hygiene expectations, TP/FP/FN
classification, and precision/recall for the validation set only.
"""

from __future__ import annotations

import json
import re
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from validation.inventory import (
    FactClassification,
    compute_precision_recall,
)

HYGIENE_RULE_IDS: tuple[str, ...] = (
    "dependency.unresolved-version",
    "dependency.mutable-version",
    "dependency.unbounded-requirement",
    "dependency.conflicting-exact-versions",
    "dependency.duplicate-declaration",
)


class DependencyEcosystemLabel(StrEnum):
    MAVEN = "maven"
    GRADLE = "gradle"
    PYTHON = "python"
    COMPOSER = "composer"
    NUGET = "nuget"
    NPM = "npm"
    UNKNOWN = "unknown"
    OTHER = "other"


class DependencyManifestExpectation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    ecosystem: str | None = None
    manifest_type: str | None = None
    parse_status: str | None = None
    declaration_count: int | None = Field(default=None, ge=0)
    rationale: str = ""


class DependencyForbiddenManifestExpectation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    path_pattern: str
    rationale: str = ""


class DependencyFindingExpectation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    path: str | None = None
    path_pattern: str | None = None
    dependency_name: str | None = None
    dependency_pattern: str | None = None
    declared_version: str | None = None
    expected_count: int | None = Field(default=None, ge=0)
    severity: str | None = None
    confidence: str | None = None
    rationale: str = ""


class DependencyRuleCountRange(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    minimum: int | None = Field(default=None, ge=0)
    maximum: int | None = Field(default=None, ge=0)
    exact: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _validate_range(self) -> DependencyRuleCountRange:
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


class DependencyExpectation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    required_manifests: tuple[DependencyManifestExpectation, ...] = ()
    forbidden_manifests: tuple[DependencyForbiddenManifestExpectation, ...] = ()
    required_findings: tuple[DependencyFindingExpectation, ...] = ()
    forbidden_findings: tuple[DependencyFindingExpectation, ...] = ()
    allowed_findings: tuple[DependencyFindingExpectation, ...] = ()
    expected_rule_ids: tuple[str, ...] = ()
    forbidden_rule_ids: tuple[str, ...] = ()
    expected_count_ranges: tuple[DependencyRuleCountRange, ...] = ()
    expected_parse_failures: tuple[str, ...] = ()
    expected_partial_parses: tuple[str, ...] = ()
    expected_limitations: tuple[str, ...] = ()
    maximum_false_positive_count: int | None = Field(default=None, ge=0)
    forbidden_conclusions: tuple[str, ...] = ()
    not_applicable_rule_ids: tuple[str, ...] = ()
    evidence_notes: str | None = None

    @model_validator(mode="after")
    def _reject_contradictions(self) -> DependencyExpectation:
        required_any = {item.rule_id for item in self.required_findings} | set(
            self.expected_rule_ids
        )
        overlap = sorted(required_any & set(self.forbidden_rule_ids))
        if overlap:
            raise ValueError(f"contradictory dependency rule expectations: {overlap}")
        required_global = set(self.expected_rule_ids) | {
            item.rule_id
            for item in self.required_findings
            if not item.path
            and not item.path_pattern
            and not item.dependency_name
            and not item.dependency_pattern
        }
        forbidden_global = set(self.forbidden_rule_ids) | {
            item.rule_id
            for item in self.forbidden_findings
            if not item.path
            and not item.path_pattern
            and not item.dependency_name
            and not item.dependency_pattern
        }
        overlap2 = sorted(required_global & forbidden_global)
        if overlap2:
            raise ValueError(f"contradictory dependency rule expectations: {overlap2}")
        required_paths = {_norm_path(item.path) for item in self.required_manifests}
        for forb in self.forbidden_manifests:
            for path in required_paths:
                if re.search(forb.path_pattern, path):
                    raise ValueError(
                        "contradictory dependency manifest expectations: "
                        f"{path!r} matches forbidden pattern {forb.path_pattern!r}"
                    )
        return self


class DependencyManifestActual(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    ecosystem: str | None = None
    manifest_type: str | None = None
    parse_status: str | None = None
    declaration_count: int | None = None
    evidence_id: str | None = None
    source_role: str | None = None


class DependencyFindingActual(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    finding_id: str | None = None
    path: str | None = None
    dependency_name: str | None = None
    declared_version: str | None = None
    ecosystem: str | None = None
    severity: str | None = None
    confidence: str | None = None
    evidence_ids: tuple[str, ...] = ()
    line_start: int | None = None


class ClassifiedDependencyFact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    rule_id: str
    classification: FactClassification
    expectation: str
    actual: str
    diagnostic: str
    ecosystem: str | None = None
    path: str | None = None


class DependencyRuleMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    ecosystem: str | None = None
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    ambiguous: int = 0
    precision: float | None = None
    recall: float | None = None
    unavailable_reason: str | None = None


class DependencyValidationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    repository_id: str
    classifications: tuple[ClassifiedDependencyFact, ...] = ()
    per_rule_metrics: tuple[DependencyRuleMetrics, ...] = ()
    per_ecosystem_metrics: tuple[DependencyRuleMetrics, ...] = ()
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    ambiguous: int = 0
    precision: float | None = None
    recall: float | None = None
    unsupported_claim_failures: tuple[str, ...] = ()
    path_failures: tuple[str, ...] = ()
    parse_coverage_failures: tuple[str, ...] = ()
    passed: bool = True
    diagnostics: tuple[str, ...] = ()


class AggregateDependencyMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    repository_count: int = 0
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    ambiguous: int = 0
    precision: float | None = None
    recall: float | None = None
    per_rule: tuple[DependencyRuleMetrics, ...] = ()
    per_ecosystem: tuple[DependencyRuleMetrics, ...] = ()
    per_repository: tuple[DependencyValidationResult, ...] = ()


def extract_dependency_findings(
    findings: list[Any] | tuple[Any, ...],
) -> tuple[DependencyFindingActual, ...]:
    rows: list[DependencyFindingActual] = []
    for item in findings:
        if not isinstance(item, dict):
            continue
        rule_id = str(item.get("rule_id") or "").strip()
        if not rule_id.startswith("dependency."):
            continue
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        path = (
            metadata.get("path")
            or item.get("path")
            or item.get("file")
            or _first_evidence_path(item.get("evidence"))
        )
        dependency_name = (
            metadata.get("normalized_identity")
            or metadata.get("original_identity")
            or metadata.get("dependency_name")
        )
        declared_version = (
            metadata.get("raw_version")
            or metadata.get("declared_version")
            or metadata.get("mutable_expression")
            or metadata.get("unresolved_expression")
            or metadata.get("resolved_version_local")
        )
        evidence_ids: list[str] = []
        for ref in item.get("evidence_refs") or []:
            if isinstance(ref, dict) and ref.get("evidence_id"):
                evidence_ids.append(str(ref["evidence_id"]))
        for evidence in item.get("evidence") or []:
            if isinstance(evidence, dict):
                eid = evidence.get("source_id") or evidence.get("evidence_id") or evidence.get("id")
                if eid:
                    evidence_ids.append(str(eid))
        if metadata.get("evidence_id"):
            evidence_ids.append(str(metadata["evidence_id"]))
        if item.get("primary_evidence_id"):
            evidence_ids.append(str(item["primary_evidence_id"]))
        line_start = _as_int(metadata.get("line_start"))
        rows.append(
            DependencyFindingActual(
                rule_id=rule_id,
                finding_id=str(item.get("id")) if item.get("id") else None,
                path=str(path) if path else None,
                dependency_name=str(dependency_name) if dependency_name else None,
                declared_version=str(declared_version) if declared_version else None,
                ecosystem=str(metadata["ecosystem"]).lower() if metadata.get("ecosystem") else None,
                severity=str(item.get("severity")).lower() if item.get("severity") else None,
                confidence=(
                    str(metadata.get("confidence") or item.get("confidence")).lower()
                    if (metadata.get("confidence") or item.get("confidence"))
                    else None
                ),
                evidence_ids=tuple(sorted(set(evidence_ids))),
                line_start=line_start,
            )
        )
    return tuple(rows)


def extract_dependency_manifests(
    document: dict[str, Any],
    *,
    artifact_paths: dict[str, str] | None = None,
) -> tuple[DependencyManifestActual, ...]:
    """Extract manifest inventory from sidecar or report dependency section."""

    rows: list[DependencyManifestActual] = []
    sidecar = _load_dependency_assessment(artifact_paths)
    if sidecar is not None:
        inventory = sidecar.get("manifest_inventory")
        entries = ()
        if isinstance(inventory, dict):
            entries = inventory.get("entries") or ()
        elif isinstance(inventory, list):
            entries = inventory
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            path = entry.get("path")
            if not path:
                continue
            rows.append(
                DependencyManifestActual(
                    path=_norm_path(str(path)),
                    ecosystem=_norm_ecosystem(entry.get("ecosystem")),
                    manifest_type=str(entry["manifest_type"]) if entry.get("manifest_type") else None,
                    parse_status=(
                        str(entry["parse_status"]).lower() if entry.get("parse_status") else None
                    ),
                    declaration_count=_as_int(entry.get("declaration_count")),
                    evidence_id=str(entry["evidence_id"]) if entry.get("evidence_id") else None,
                    source_role=str(entry["source_role"]) if entry.get("source_role") else None,
                )
            )
        if rows:
            return tuple(sorted(rows, key=lambda item: item.path))

    assessment = document.get("assessment") if isinstance(document.get("assessment"), dict) else {}
    dependency = (
        assessment.get("dependency") if isinstance(assessment.get("dependency"), dict) else {}
    )
    for hotspot in dependency.get("manifest_hotspots") or []:
        if not isinstance(hotspot, dict):
            continue
        path = hotspot.get("path")
        if not path:
            continue
        rows.append(
            DependencyManifestActual(
                path=_norm_path(str(path)),
                ecosystem=_norm_ecosystem(hotspot.get("ecosystem")),
                manifest_type=(
                    str(hotspot["manifest_type"]) if hotspot.get("manifest_type") else None
                ),
                parse_status=(
                    str(hotspot["parse_status"]).lower() if hotspot.get("parse_status") else None
                ),
                declaration_count=_as_int(
                    hotspot.get("declaration_count") or hotspot.get("declarations")
                ),
                evidence_id=str(hotspot["evidence_id"]) if hotspot.get("evidence_id") else None,
                source_role=str(hotspot["source_role"]) if hotspot.get("source_role") else None,
            )
        )
    return tuple(sorted(rows, key=lambda item: item.path))


def discover_dependency_artifact_paths(report_path: Path) -> dict[str, str]:
    """Locate dependency sidecars next to report.json when present."""

    found: dict[str, str] = {}
    parent = report_path.parent
    assessment = parent / "heads" / "dependencies.json"
    if not assessment.is_file():
        assessment = parent / "dependency-assessment.json"
    evidence = parent / "dependency-evidence.json"
    if assessment.is_file():
        found["dependency-assessment.json"] = str(assessment)
    if evidence.is_file():
        found["dependency-evidence.json"] = str(evidence)
    return found


def validate_dependency_precision(
    *,
    repository_id: str,
    expectation: DependencyExpectation,
    actual_findings: tuple[DependencyFindingActual, ...] | list[DependencyFindingActual],
    actual_manifests: tuple[DependencyManifestActual, ...] | list[DependencyManifestActual] = (),
    artifact_texts: dict[str, str] | None = None,
    limitation_texts: tuple[str, ...] | list[str] = (),
) -> DependencyValidationResult:
    actual = tuple(actual_findings)
    manifests = tuple(actual_manifests)
    classifications: list[ClassifiedDependencyFact] = []
    allowed_rule_ids = {item.rule_id for item in expectation.allowed_findings}
    structured_required = {item.rule_id for item in expectation.required_findings}

    for req in expectation.required_manifests:
        matches = [item for item in manifests if _manifest_matches(req, item)]
        if matches:
            match = matches[0]
            classifications.append(
                ClassifiedDependencyFact(
                    name=f"manifest:{req.path}",
                    rule_id="dependency.manifest",
                    classification=FactClassification.TRUE_POSITIVE,
                    expectation=_manifest_expect_text(req),
                    actual=(
                        f"path={match.path} ecosystem={match.ecosystem} "
                        f"status={match.parse_status} count={match.declaration_count}"
                    ),
                    diagnostic=req.rationale or "required dependency manifest matched",
                    ecosystem=match.ecosystem,
                    path=match.path,
                )
            )
        else:
            classifications.append(
                ClassifiedDependencyFact(
                    name=f"manifest:{req.path}",
                    rule_id="dependency.manifest",
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=_manifest_expect_text(req),
                    actual="absent",
                    diagnostic=req.rationale or "required dependency manifest missing",
                    ecosystem=req.ecosystem,
                    path=req.path,
                )
            )

    for forb in expectation.forbidden_manifests:
        matches = [
            item for item in manifests if re.search(forb.path_pattern, item.path or "")
        ]
        for match in matches:
            classifications.append(
                ClassifiedDependencyFact(
                    name=f"manifest:{match.path}",
                    rule_id="dependency.manifest",
                    classification=FactClassification.FALSE_POSITIVE,
                    expectation=f"forbidden manifest pattern {forb.path_pattern}",
                    actual=f"path={match.path}",
                    diagnostic=forb.rationale or "forbidden dependency manifest present",
                    ecosystem=match.ecosystem,
                    path=match.path,
                )
            )

    for req in expectation.required_findings:
        matches = [item for item in actual if _finding_matches(req, item)]
        expected_count = req.expected_count if req.expected_count is not None else 1
        if len(matches) >= expected_count:
            classifications.append(
                ClassifiedDependencyFact(
                    name=req.rule_id,
                    rule_id=req.rule_id,
                    classification=FactClassification.TRUE_POSITIVE,
                    expectation=_finding_expect_text(req),
                    actual=f"count={len(matches)}",
                    diagnostic=req.rationale or "required dependency finding matched",
                    ecosystem=matches[0].ecosystem,
                    path=req.path or matches[0].path,
                )
            )
        else:
            classifications.append(
                ClassifiedDependencyFact(
                    name=req.rule_id,
                    rule_id=req.rule_id,
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=_finding_expect_text(req),
                    actual=f"count={len(matches)}",
                    diagnostic=req.rationale or "required dependency finding missing",
                    ecosystem=None,
                    path=req.path,
                )
            )

    for rule_id in expectation.expected_rule_ids:
        if rule_id in structured_required:
            continue
        present = [item for item in actual if item.rule_id == rule_id]
        if present:
            classifications.append(
                ClassifiedDependencyFact(
                    name=rule_id,
                    rule_id=rule_id,
                    classification=FactClassification.TRUE_POSITIVE,
                    expectation=f"required rule {rule_id}",
                    actual=f"count={len(present)}",
                    diagnostic="required rule present",
                    ecosystem=present[0].ecosystem,
                    path=present[0].path,
                )
            )
        else:
            classifications.append(
                ClassifiedDependencyFact(
                    name=rule_id,
                    rule_id=rule_id,
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=f"required rule {rule_id}",
                    actual="absent",
                    diagnostic="required rule missing",
                )
            )

    for forb in expectation.forbidden_findings:
        matches = [item for item in actual if _finding_matches(forb, item)]
        for match in matches:
            classifications.append(
                ClassifiedDependencyFact(
                    name=forb.rule_id,
                    rule_id=forb.rule_id,
                    classification=FactClassification.FALSE_POSITIVE,
                    expectation=_finding_expect_text(forb),
                    actual=(
                        f"path={match.path!r} dependency={match.dependency_name!r} "
                        f"version={match.declared_version!r}"
                    ),
                    diagnostic=forb.rationale or "forbidden dependency finding present",
                    ecosystem=match.ecosystem,
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
                    ClassifiedDependencyFact(
                        name=rule_id,
                        rule_id=rule_id,
                        classification=FactClassification.AMBIGUOUS,
                        expectation="allowed overlap",
                        actual=f"path={match.path!r}",
                        diagnostic="allowed finding excluded from FP scoring",
                        ecosystem=match.ecosystem,
                        path=match.path,
                    )
                )
            else:
                classifications.append(
                    ClassifiedDependencyFact(
                        name=rule_id,
                        rule_id=rule_id,
                        classification=FactClassification.FALSE_POSITIVE,
                        expectation=f"forbidden rule {rule_id}",
                        actual=f"path={match.path!r} dependency={match.dependency_name!r}",
                        diagnostic="forbidden rule present",
                        ecosystem=match.ecosystem,
                        path=match.path,
                    )
                )

    for allowed in expectation.allowed_findings:
        matches = [item for item in actual if _finding_matches(allowed, item)]
        if matches and allowed.rule_id not in structured_required:
            classifications.append(
                ClassifiedDependencyFact(
                    name=allowed.rule_id,
                    rule_id=allowed.rule_id,
                    classification=FactClassification.AMBIGUOUS,
                    expectation=allowed.rationale or "allowed finding",
                    actual=f"count={len(matches)}",
                    diagnostic="allowed finding not scored as TP",
                    ecosystem=matches[0].ecosystem,
                    path=allowed.path or matches[0].path,
                )
            )

    for range_spec in expectation.expected_count_ranges:
        count = sum(1 for item in actual if item.rule_id == range_spec.rule_id)
        if not range_spec.contains(count):
            classifications.append(
                ClassifiedDependencyFact(
                    name=range_spec.rule_id,
                    rule_id=range_spec.rule_id,
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=f"count {range_spec.describe()}",
                    actual=f"count={count}",
                    diagnostic="rule count outside range",
                )
            )

    for rule_id in expectation.not_applicable_rule_ids:
        if any(item.rule_id == rule_id for item in actual):
            classifications.append(
                ClassifiedDependencyFact(
                    name=rule_id,
                    rule_id=rule_id,
                    classification=FactClassification.FALSE_POSITIVE,
                    expectation="not applicable",
                    actual="present",
                    diagnostic="not-applicable rule emitted a finding",
                )
            )
        else:
            classifications.append(
                ClassifiedDependencyFact(
                    name=rule_id,
                    rule_id=rule_id,
                    classification=FactClassification.NOT_APPLICABLE,
                    expectation="not applicable",
                    actual="absent",
                    diagnostic="rule marked not_applicable",
                )
            )

    parse_failures: list[str] = []
    for path in expectation.expected_partial_parses:
        matches = [
            item
            for item in manifests
            if _norm_path(item.path) == _norm_path(path)
            and (item.parse_status or "").lower()
            in {"partially_succeeded", "partial", "partially-succeeded"}
        ]
        if not matches:
            parse_failures.append(f"expected_partial_parse_missing:{path}")
    for path in expectation.expected_parse_failures:
        matches = [
            item
            for item in manifests
            if _norm_path(item.path) == _norm_path(path)
            and (item.parse_status or "").lower() == "failed"
        ]
        if not matches:
            parse_failures.append(f"expected_parse_failure_missing:{path}")
    # Zero findings must not imply healthy when parse failures exist.
    failed_or_partial = [
        item
        for item in manifests
        if (item.parse_status or "").lower()
        in {"failed", "partially_succeeded", "partial", "partially-succeeded"}
    ]
    if failed_or_partial and not actual and expectation.forbidden_conclusions:
        # Soft signal only when conclusions claim health — checked below.
        pass

    path_failures: list[str] = []
    for item in actual:
        if item.path and (item.path.startswith("/") or item.path.startswith("\\")):
            path_failures.append(f"absolute_path:{item.rule_id}:{item.path}")
        if item.path and "/" not in item.path.replace("\\", "/") and item.path.count(".") == 0:
            # Basename-only for multi-segment manifests is suspicious; allow
            # known single-segment manifests (pom.xml, requirements.txt, …).
            basename_ok = item.path.lower() in {
                "pom.xml",
                "build.gradle",
                "build.gradle.kts",
                "pyproject.toml",
                "requirements.txt",
                "composer.json",
                "packages.config",
            }
            if not basename_ok and item.path.lower().endswith(
                (".csproj", ".props", ".json", ".toml", ".xml", ".gradle")
            ):
                pass  # single-segment manifest filenames are repository-relative
        if not item.evidence_ids:
            path_failures.append(f"missing_evidence:{item.rule_id}:{item.finding_id}")

    for item in manifests:
        if item.path.startswith("/") or item.path.startswith("\\"):
            path_failures.append(f"absolute_manifest_path:{item.path}")

    limitation_blob = "\n".join(limitation_texts).lower()
    for expected_limit in expectation.expected_limitations:
        if expected_limit.lower() not in limitation_blob:
            parse_failures.append(f"expected_limitation_missing:{expected_limit}")

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
    per_ecosystem = _per_ecosystem_metrics(classifications)
    diagnostics = [
        f"{item.classification.value}:{item.rule_id}:{item.diagnostic}"
        for item in classifications
        if item.classification
        in {FactClassification.FALSE_POSITIVE, FactClassification.FALSE_NEGATIVE}
    ]
    diagnostics.extend(f"unsupported:{item}" for item in unsupported)
    diagnostics.extend(f"path:{item}" for item in path_failures)
    diagnostics.extend(f"parse:{item}" for item in parse_failures)

    passed = fp == 0 and fn == 0 and not unsupported and not path_failures and not parse_failures
    if expectation.maximum_false_positive_count is not None:
        passed = passed and fp <= expectation.maximum_false_positive_count

    return DependencyValidationResult(
        repository_id=repository_id,
        classifications=tuple(classifications),
        per_rule_metrics=per_rule,
        per_ecosystem_metrics=per_ecosystem,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        ambiguous=amb,
        precision=precision,
        recall=recall,
        unsupported_claim_failures=tuple(unsupported),
        path_failures=tuple(path_failures),
        parse_coverage_failures=tuple(parse_failures),
        passed=passed,
        diagnostics=tuple(diagnostics),
    )


def aggregate_dependency_results(
    results: list[DependencyValidationResult] | tuple[DependencyValidationResult, ...],
) -> AggregateDependencyMetrics:
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
    by_ecosystem: dict[str, list[int]] = {}
    for result in results_t:
        for metrics in result.per_rule_metrics:
            bucket = by_rule.setdefault(metrics.rule_id, [0, 0, 0, 0])
            bucket[0] += metrics.true_positives
            bucket[1] += metrics.false_positives
            bucket[2] += metrics.false_negatives
            bucket[3] += metrics.ambiguous
        for metrics in result.per_ecosystem_metrics:
            key = metrics.ecosystem or metrics.rule_id
            bucket = by_ecosystem.setdefault(key, [0, 0, 0, 0])
            bucket[0] += metrics.true_positives
            bucket[1] += metrics.false_positives
            bucket[2] += metrics.false_negatives
            bucket[3] += metrics.ambiguous
    per_rule = []
    for rule_id, (rtp, rfp, rfn, ramb) in sorted(by_rule.items()):
        rprec, rrec, rreason = compute_precision_recall(
            true_positives=rtp, false_positives=rfp, false_negatives=rfn
        )
        per_rule.append(
            DependencyRuleMetrics(
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
    per_ecosystem = []
    for eco, (rtp, rfp, rfn, ramb) in sorted(by_ecosystem.items()):
        rprec, rrec, rreason = compute_precision_recall(
            true_positives=rtp, false_positives=rfp, false_negatives=rfn
        )
        per_ecosystem.append(
            DependencyRuleMetrics(
                rule_id=eco,
                ecosystem=eco,
                true_positives=rtp,
                false_positives=rfp,
                false_negatives=rfn,
                ambiguous=ramb,
                precision=rprec,
                recall=rrec,
                unavailable_reason=rreason,
            )
        )
    return AggregateDependencyMetrics(
        repository_count=len(results_t),
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        ambiguous=amb,
        precision=precision,
        recall=recall,
        per_rule=tuple(per_rule),
        per_ecosystem=tuple(per_ecosystem),
        per_repository=results_t,
    )


def _load_dependency_assessment(
    artifact_paths: dict[str, str] | None,
) -> dict[str, Any] | None:
    if not artifact_paths:
        return None
    path_str = artifact_paths.get("dependency-assessment.json")
    if not path_str:
        return None
    path = Path(path_str)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _manifest_matches(
    expectation: DependencyManifestExpectation,
    actual: DependencyManifestActual,
) -> bool:
    if _norm_path(actual.path) != _norm_path(expectation.path):
        return False
    if expectation.ecosystem and _norm(actual.ecosystem or "") != _norm(expectation.ecosystem):
        return False
    if expectation.manifest_type and _norm(actual.manifest_type or "") != _norm(
        expectation.manifest_type
    ):
        return False
    if expectation.parse_status and _norm(actual.parse_status or "") != _norm(
        expectation.parse_status
    ):
        return False
    if (
        expectation.declaration_count is not None
        and actual.declaration_count != expectation.declaration_count
    ):
        return False
    return True


def _finding_matches(
    expectation: DependencyFindingExpectation,
    actual: DependencyFindingActual,
) -> bool:
    if actual.rule_id != expectation.rule_id:
        return False
    if expectation.path and _norm_path(actual.path or "") != _norm_path(expectation.path):
        return False
    if expectation.path_pattern:
        if not actual.path or not re.search(expectation.path_pattern, actual.path):
            return False
    if expectation.dependency_name and _norm(actual.dependency_name or "") != _norm(
        expectation.dependency_name
    ):
        return False
    if expectation.dependency_pattern:
        if not actual.dependency_name or not re.search(
            expectation.dependency_pattern, actual.dependency_name
        ):
            return False
    if expectation.declared_version is not None:
        if _norm(actual.declared_version or "") != _norm(expectation.declared_version):
            return False
    if expectation.severity and _norm(actual.severity or "") != _norm(expectation.severity):
        return False
    return True


def _manifest_expect_text(item: DependencyManifestExpectation) -> str:
    parts = [f"path={item.path}"]
    if item.ecosystem:
        parts.append(f"ecosystem={item.ecosystem}")
    if item.manifest_type:
        parts.append(f"type={item.manifest_type}")
    if item.parse_status:
        parts.append(f"status={item.parse_status}")
    return ",".join(parts)


def _finding_expect_text(item: DependencyFindingExpectation) -> str:
    parts = [f"rule={item.rule_id}"]
    if item.path:
        parts.append(f"path={item.path}")
    if item.dependency_name:
        parts.append(f"dependency={item.dependency_name}")
    if item.declared_version is not None:
        parts.append(f"version={item.declared_version}")
    return ",".join(parts)


def _per_rule_metrics(
    classifications: list[ClassifiedDependencyFact],
) -> tuple[DependencyRuleMetrics, ...]:
    rules = sorted({item.rule_id for item in classifications})
    metrics: list[DependencyRuleMetrics] = []
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
            DependencyRuleMetrics(
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


def _per_ecosystem_metrics(
    classifications: list[ClassifiedDependencyFact],
) -> tuple[DependencyRuleMetrics, ...]:
    ecosystems = sorted({item.ecosystem or "unknown" for item in classifications})
    metrics: list[DependencyRuleMetrics] = []
    for ecosystem in ecosystems:
        scoped = [item for item in classifications if (item.ecosystem or "unknown") == ecosystem]
        tp = sum(1 for item in scoped if item.classification is FactClassification.TRUE_POSITIVE)
        fp = sum(1 for item in scoped if item.classification is FactClassification.FALSE_POSITIVE)
        fn = sum(1 for item in scoped if item.classification is FactClassification.FALSE_NEGATIVE)
        amb = sum(1 for item in scoped if item.classification is FactClassification.AMBIGUOUS)
        precision, recall, reason = compute_precision_recall(
            true_positives=tp, false_positives=fp, false_negatives=fn
        )
        metrics.append(
            DependencyRuleMetrics(
                rule_id=ecosystem,
                ecosystem=ecosystem,
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


def _as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _norm_ecosystem(value: Any) -> str | None:
    if value is None:
        return None
    raw = str(value).strip().lower()
    if raw in {"pip", "pypi"}:
        return DependencyEcosystemLabel.PYTHON.value
    if raw in DependencyEcosystemLabel._value2member_map_:
        return raw
    return raw or None


def _is_disclaimer_negation(text: str, claim: str) -> bool:
    patterns = (
        rf"do not certify {re.escape(claim)}",
        rf"does not certify {re.escape(claim)}",
        rf"were not performed",
        rf"were not evaluated",
        rf"were not assessed",
        rf"not performed",
        rf"registry, vulnerability, license, freshness",
        rf"out of scope",
        rf"no dependency declaration-hygiene findings were produced",
    )
    return any(re.search(pattern, text) for pattern in patterns)


def _norm(value: str) -> str:
    return value.strip().lower()


def _norm_path(value: str) -> str:
    return value.replace("\\", "/").strip().lstrip("./")
