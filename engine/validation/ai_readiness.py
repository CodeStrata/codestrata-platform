"""AI Readiness precision validation (Epic 4 Slice 4.8).

Evidence-authored AI Readiness signal/finding expectations, TP/FP/FN classification,
and precision/recall for the validation set only.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from validation.inventory import (
    FactClassification,
    compute_precision_recall,
)

AI_READINESS_RULE_IDS: tuple[str, ...] = (
    "ai_readiness.ai-001",
    "ai_readiness.ai-002",
    "ai_readiness.ai-003",
    "ai_readiness.ai-010",
    "ai_readiness.ai-011",
    "ai_readiness.ai-020",
    "ai_readiness.ai-021",
    "ai_readiness.ai-022",
    "ai_readiness.ai-030",
    "ai_readiness.ai-031",
    "ai_readiness.ai-032",
    "ai_readiness.ai-040",
    "ai_readiness.ai-041",
    "ai_readiness.ai-050",
    "ai_readiness.ai-051",
    "ai_readiness.ai-060",
    "ai_readiness.ai-061",
)

AI_READINESS_FAMILIES: tuple[str, ...] = (
    "api_boundary",
    "documentation",
    "data_retrieval",
    "ai_integration",
    "tool_mcp",
    "workflow_agent",
    "observability_governance",
)

_REPORT_FAMILY_ALIASES: dict[str, str] = {
    "api_boundary": "api_boundary",
    "api_boundaries": "api_boundary",
    "documentation": "documentation",
    "documentation_metadata": "documentation",
    "data_retrieval": "data_retrieval",
    "ai_integration": "ai_integration",
    "ai_integrations": "ai_integration",
    "tool_mcp": "tool_mcp",
    "workflow_agent": "workflow_agent",
    "workflow_agents": "workflow_agent",
    "observability_governance": "observability_governance",
}

_FACT_KEY_TO_FAMILY: dict[str, str] = {
    "api_boundary_facts": "api_boundary",
    "documentation_facts": "documentation",
    "data_retrieval_facts": "data_retrieval",
    "ai_integration_facts": "ai_integration",
    "tool_mcp_facts": "tool_mcp",
    "workflow_agent_facts": "workflow_agent",
    "observability_governance_facts": "observability_governance",
}


class AiReadinessFamilyExpectation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    family_id: str
    rationale: str = ""


class AiReadinessSignalExpectation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    family_id: str
    signal_kind: str | None = None
    path: str | None = None
    path_pattern: str | None = None
    signal_pattern: str | None = None
    expected_count: int | None = Field(default=None, ge=0)
    rationale: str = ""


class AiReadinessFindingExpectation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str | None = None
    path: str | None = None
    path_pattern: str | None = None
    expected_count: int | None = Field(default=None, ge=0)
    severity: str | None = None
    confidence: str | None = None
    rationale: str = ""


class AiReadinessRecommendationExpectation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    category: str | None = None
    title_pattern: str | None = None
    supporting_rule_ids: tuple[str, ...] = ()
    rationale: str = ""


class AiReadinessRuleCountRange(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    minimum: int | None = Field(default=None, ge=0)
    maximum: int | None = Field(default=None, ge=0)
    exact: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _validate_range(self) -> AiReadinessRuleCountRange:
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


class AiReadinessExpectation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    required_signal_families: tuple[AiReadinessFamilyExpectation, ...] = ()
    forbidden_signal_families: tuple[AiReadinessFamilyExpectation, ...] = ()
    required_signals: tuple[AiReadinessSignalExpectation, ...] = ()
    forbidden_signals: tuple[AiReadinessSignalExpectation, ...] = ()
    required_findings: tuple[AiReadinessFindingExpectation, ...] = ()
    forbidden_findings: tuple[AiReadinessFindingExpectation, ...] = ()
    allowed_findings: tuple[AiReadinessFindingExpectation, ...] = ()
    required_recommendations: tuple[AiReadinessRecommendationExpectation, ...] = ()
    forbidden_recommendations: tuple[AiReadinessRecommendationExpectation, ...] = ()
    expected_rule_ids: tuple[str, ...] = ()
    forbidden_rule_ids: tuple[str, ...] = ()
    expected_count_ranges: tuple[AiReadinessRuleCountRange, ...] = ()
    expected_coverage_state: str | None = None
    expected_limitations: tuple[str, ...] = ()
    maximum_false_positive_count: int | None = Field(default=None, ge=0)
    forbidden_conclusions: tuple[str, ...] = ()
    not_applicable_rule_ids: tuple[str, ...] = ()
    evidence_notes: str | None = None

    @model_validator(mode="after")
    def _reject_contradictions(self) -> AiReadinessExpectation:
        required_any = {
            item.rule_id for item in self.required_findings if item.rule_id
        } | set(self.expected_rule_ids)
        overlap = sorted(required_any & set(self.forbidden_rule_ids))
        if overlap:
            raise ValueError(f"contradictory ai_readiness rule expectations: {overlap}")
        required_global = set(self.expected_rule_ids) | {
            item.rule_id
            for item in self.required_findings
            if item.rule_id
            and not item.path
            and not item.path_pattern
        }
        forbidden_global = set(self.forbidden_rule_ids) | {
            item.rule_id
            for item in self.forbidden_findings
            if item.rule_id
            and not item.path
            and not item.path_pattern
        }
        overlap2 = sorted(required_global & forbidden_global)
        if overlap2:
            raise ValueError(f"contradictory ai_readiness rule expectations: {overlap2}")
        required_families = {item.family_id for item in self.required_signal_families}
        forbidden_families = {item.family_id for item in self.forbidden_signal_families}
        family_overlap = sorted(required_families & forbidden_families)
        if family_overlap:
            raise ValueError(
                f"contradictory ai_readiness family expectations: {family_overlap}"
            )
        return self


class AiReadinessSignalActual(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    family_id: str
    signal_kind: str | None = None
    path: str | None = None
    confirmation_level: str | None = None
    evidence_id: str | None = None


class AiReadinessFindingActual(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    finding_id: str | None = None
    path: str | None = None
    severity: str | None = None
    confidence: str | None = None
    evidence_ids: tuple[str, ...] = ()
    family_id: str | None = None


class AiReadinessRecommendationActual(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    title: str
    category: str | None = None
    recommendation_id: str | None = None
    supporting_rule_ids: tuple[str, ...] = ()


class ClassifiedAiReadinessFact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    rule_id: str
    classification: FactClassification
    expectation: str
    actual: str
    diagnostic: str
    family_id: str | None = None
    path: str | None = None


class AiReadinessRuleMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    family_id: str | None = None
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    ambiguous: int = 0
    precision: float | None = None
    recall: float | None = None
    unavailable_reason: str | None = None


class AiReadinessValidationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    repository_id: str
    classifications: tuple[ClassifiedAiReadinessFact, ...] = ()
    per_rule_metrics: tuple[AiReadinessRuleMetrics, ...] = ()
    per_family_metrics: tuple[AiReadinessRuleMetrics, ...] = ()
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


class AggregateAiReadinessMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    repository_count: int = 0
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    ambiguous: int = 0
    precision: float | None = None
    recall: float | None = None
    per_rule: tuple[AiReadinessRuleMetrics, ...] = ()
    per_family: tuple[AiReadinessRuleMetrics, ...] = ()
    per_repository: tuple[AiReadinessValidationResult, ...] = ()


def extract_ai_readiness_findings(
    findings: list[Any] | tuple[Any, ...],
) -> tuple[AiReadinessFindingActual, ...]:
    rows: list[AiReadinessFindingActual] = []
    for item in findings:
        if not isinstance(item, dict):
            continue
        rule_id = str(item.get("rule_id") or "").strip()
        if not rule_id.startswith("ai_readiness."):
            continue
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        path = (
            metadata.get("path")
            or item.get("path")
            or item.get("file_path")
            or item.get("file")
            or _first_evidence_path(item.get("evidence"))
        )
        evidence_ids: list[str] = []
        for ref in item.get("evidence_refs") or []:
            if isinstance(ref, dict) and ref.get("evidence_id"):
                evidence_ids.append(str(ref["evidence_id"]))
            elif isinstance(ref, str) and ref.strip():
                evidence_ids.append(ref.strip())
        for evidence in item.get("evidence") or []:
            if isinstance(evidence, dict):
                eid = (
                    evidence.get("source_id")
                    or evidence.get("evidence_id")
                    or evidence.get("id")
                )
                if eid:
                    evidence_ids.append(str(eid))
        if metadata.get("evidence_id"):
            evidence_ids.append(str(metadata["evidence_id"]))
        if item.get("primary_evidence_id"):
            evidence_ids.append(str(item["primary_evidence_id"]))
        for eid in item.get("synthesized_from_evidence_ids") or []:
            if eid:
                evidence_ids.append(str(eid))
        family_raw = (
            metadata.get("family_id")
            or metadata.get("family")
            or metadata.get("ai_readiness_family")
        )
        family_id = _normalize_family_id(family_raw)
        if family_id and family_id not in AI_READINESS_FAMILIES:
            family_id = None
        rows.append(
            AiReadinessFindingActual(
                rule_id=rule_id,
                finding_id=str(item.get("id")) if item.get("id") else None,
                path=str(path) if path else None,
                severity=str(item.get("severity")).lower() if item.get("severity") else None,
                confidence=(
                    str(metadata.get("confidence") or item.get("confidence")).lower()
                    if (metadata.get("confidence") or item.get("confidence"))
                    else None
                ),
                evidence_ids=tuple(sorted(set(evidence_ids))),
                family_id=family_id,
            )
        )
    return tuple(rows)


def extract_ai_readiness_signals(
    document: dict[str, Any],
    *,
    artifact_paths: dict[str, str] | None = None,
) -> tuple[AiReadinessSignalActual, ...]:
    """Extract AI Readiness signals from sidecar or report ai_readiness section."""

    rows: list[AiReadinessSignalActual] = []
    sidecar = _load_ai_readiness_evidence(artifact_paths)
    if sidecar is not None:
        for fact_key, family_id in _FACT_KEY_TO_FAMILY.items():
            for fact in sidecar.get(fact_key) or []:
                if not isinstance(fact, dict):
                    continue
                signal_kind = _signal_kind_from_fact(family_id, fact)
                path = fact.get("path")
                rows.append(
                    AiReadinessSignalActual(
                        family_id=family_id,
                        signal_kind=signal_kind,
                        path=_norm_path(str(path)) if path else None,
                        confirmation_level=(
                            str(fact["confirmation_level"]).lower()
                            if fact.get("confirmation_level")
                            else None
                        ),
                        evidence_id=(
                            str(fact["evidence_id"]) if fact.get("evidence_id") else None
                        ),
                    )
                )
        if rows:
            return tuple(
                sorted(
                    rows,
                    key=lambda item: (
                        item.family_id,
                        item.path or "",
                        item.signal_kind or "",
                        item.evidence_id or "",
                    ),
                )
            )

    assessment = document.get("assessment") if isinstance(document.get("assessment"), dict) else {}
    ai_readiness = (
        assessment.get("ai_readiness")
        if isinstance(assessment.get("ai_readiness"), dict)
        else {}
    )
    family_summary = (
        ai_readiness.get("capability_family_summary")
        or ai_readiness.get("technology_family_summary")
    )
    if isinstance(family_summary, dict):
        for entry in family_summary.get("entries") or []:
            if not isinstance(entry, dict) or not entry.get("observed"):
                continue
            family_id = _normalize_family_id(entry.get("family_id"))
            if not family_id:
                continue
            technologies = entry.get("technologies") or entry.get("signals") or []
            if technologies:
                for tech in technologies:
                    kind = tech
                    if isinstance(tech, dict):
                        kind = tech.get("kind") or tech.get("signal_kind") or tech.get("name")
                    rows.append(
                        AiReadinessSignalActual(
                            family_id=family_id,
                            signal_kind=str(kind).lower() if kind else None,
                            path=None,
                            confirmation_level=None,
                            evidence_id=None,
                        )
                    )
            else:
                rows.append(
                    AiReadinessSignalActual(
                        family_id=family_id,
                        signal_kind=None,
                        path=None,
                        confirmation_level=None,
                        evidence_id=None,
                    )
                )
    inventory = ai_readiness.get("inventory_summary")
    if isinstance(inventory, dict) and not rows:
        for family_raw in inventory.get("families") or inventory.get("families_represented") or []:
            family_id = _normalize_family_id(family_raw)
            if family_id:
                rows.append(
                    AiReadinessSignalActual(
                        family_id=family_id,
                        signal_kind=None,
                        path=None,
                        confirmation_level=None,
                        evidence_id=None,
                    )
                )
    return tuple(
        sorted(
            rows,
            key=lambda item: (
                item.family_id,
                item.path or "",
                item.signal_kind or "",
                item.evidence_id or "",
            ),
        )
    )


def extract_ai_readiness_recommendations(
    document: dict[str, Any],
) -> tuple[AiReadinessRecommendationActual, ...]:
    """Extract AI Readiness-related recommendations from report assessment sections."""

    rows: list[AiReadinessRecommendationActual] = []
    seen: set[tuple[str, str | None]] = set()

    def _consume(items: Any, *, force_ai_readiness: bool = False) -> None:
        if not isinstance(items, list):
            return
        for item in items:
            if not isinstance(item, dict):
                continue
            title = item.get("title") or item.get("action")
            if not title:
                continue
            category = (
                item.get("category")
                or item.get("presentation_group")
                or item.get("kind")
                or item.get("audience")
            )
            rec_id = item.get("recommendation_id") or item.get("id")
            if not force_ai_readiness and not _looks_like_ai_readiness_recommendation(item):
                continue
            key = (str(title), str(rec_id) if rec_id else None)
            if key in seen:
                continue
            seen.add(key)
            rule_ids_raw = item.get("rule_ids") or item.get("supporting_rule_ids") or []
            supporting = tuple(
                str(rule_id)
                for rule_id in rule_ids_raw
                if isinstance(rule_id, str) and rule_id.strip()
            )
            rows.append(
                AiReadinessRecommendationActual(
                    title=str(title),
                    category=str(category) if category else None,
                    recommendation_id=str(rec_id) if rec_id else None,
                    supporting_rule_ids=supporting,
                )
            )

    assessment = document.get("assessment") if isinstance(document.get("assessment"), dict) else {}
    ai_readiness = (
        assessment.get("ai_readiness")
        if isinstance(assessment.get("ai_readiness"), dict)
        else {}
    )
    _consume(ai_readiness.get("recommendations"), force_ai_readiness=True)
    for group in ai_readiness.get("recommendation_groups") or []:
        if isinstance(group, dict):
            _consume(group.get("recommendations"), force_ai_readiness=True)
    _consume(assessment.get("recommendations"))
    _consume(document.get("recommendations"))
    return tuple(rows)


def discover_ai_readiness_artifact_paths(report_path: Path) -> dict[str, str]:
    """Locate AI Readiness sidecars next to report.json when present."""

    found: dict[str, str] = {}
    parent = report_path.parent
    assessment = parent / "ai-readiness-assessment.json"
    evidence = parent / "repository-ai-readiness-evidence.json"
    if assessment.is_file():
        found["ai-readiness-assessment.json"] = str(assessment)
    if evidence.is_file():
        found["repository-ai-readiness-evidence.json"] = str(evidence)
    return found


def validate_ai_readiness_precision(
    *,
    repository_id: str,
    expectation: AiReadinessExpectation,
    actual_findings: tuple[AiReadinessFindingActual, ...] | list[AiReadinessFindingActual],
    actual_signals: tuple[AiReadinessSignalActual, ...] | list[AiReadinessSignalActual] = (),
    actual_recommendations: (
        tuple[AiReadinessRecommendationActual, ...] | list[AiReadinessRecommendationActual]
    ) = (),
    artifact_texts: dict[str, str] | None = None,
    limitation_texts: tuple[str, ...] | list[str] = (),
    coverage_state: str | None = None,
) -> AiReadinessValidationResult:
    actual = tuple(actual_findings)
    signals = tuple(actual_signals)
    recommendations = tuple(actual_recommendations)
    classifications: list[ClassifiedAiReadinessFact] = []
    allowed_rule_ids = {
        item.rule_id for item in expectation.allowed_findings if item.rule_id
    }
    structured_required = {
        item.rule_id for item in expectation.required_findings if item.rule_id
    }

    for req in expectation.required_signal_families:
        family = _normalize_family_id(req.family_id) or req.family_id
        matches = [
            item for item in signals if _norm(item.family_id) == _norm(family)
        ]
        if matches:
            match = matches[0]
            classifications.append(
                ClassifiedAiReadinessFact(
                    name=f"family:{family}",
                    rule_id="ai_readiness.signal_family",
                    classification=FactClassification.TRUE_POSITIVE,
                    expectation=f"required family {family}",
                    actual=(
                        f"family={match.family_id} kind={match.signal_kind} "
                        f"level={match.confirmation_level}"
                    ),
                    diagnostic=req.rationale or "required AI Readiness signal family matched",
                    family_id=family,
                    path=match.path,
                )
            )
        else:
            classifications.append(
                ClassifiedAiReadinessFact(
                    name=f"family:{family}",
                    rule_id="ai_readiness.signal_family",
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=f"required family {family}",
                    actual="absent",
                    diagnostic=req.rationale or "required AI Readiness signal family missing",
                    family_id=family,
                )
            )

    for forb in expectation.forbidden_signal_families:
        family = _normalize_family_id(forb.family_id) or forb.family_id
        matches = [item for item in signals if _norm(item.family_id) == _norm(family)]
        for match in matches:
            classifications.append(
                ClassifiedAiReadinessFact(
                    name=f"family:{family}",
                    rule_id="ai_readiness.signal_family",
                    classification=FactClassification.FALSE_POSITIVE,
                    expectation=f"forbidden family {family}",
                    actual=f"path={match.path!r} kind={match.signal_kind!r}",
                    diagnostic=forb.rationale or "forbidden AI Readiness signal family present",
                    family_id=family,
                    path=match.path,
                )
            )

    for req in expectation.required_signals:
        matches = [item for item in signals if _signal_matches(req, item)]
        expected_count = req.expected_count if req.expected_count is not None else 1
        if len(matches) >= expected_count:
            classifications.append(
                ClassifiedAiReadinessFact(
                    name=f"signal:{req.family_id}",
                    rule_id="ai_readiness.signal",
                    classification=FactClassification.TRUE_POSITIVE,
                    expectation=_signal_expect_text(req),
                    actual=f"count={len(matches)}",
                    diagnostic=req.rationale or "required AI Readiness signal matched",
                    family_id=_normalize_family_id(req.family_id) or req.family_id,
                    path=req.path or matches[0].path,
                )
            )
        else:
            classifications.append(
                ClassifiedAiReadinessFact(
                    name=f"signal:{req.family_id}",
                    rule_id="ai_readiness.signal",
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=_signal_expect_text(req),
                    actual=f"count={len(matches)}",
                    diagnostic=req.rationale or "required AI Readiness signal missing",
                    family_id=_normalize_family_id(req.family_id) or req.family_id,
                    path=req.path,
                )
            )

    for forb in expectation.forbidden_signals:
        matches = [item for item in signals if _signal_matches(forb, item)]
        for match in matches:
            classifications.append(
                ClassifiedAiReadinessFact(
                    name=f"signal:{forb.family_id}",
                    rule_id="ai_readiness.signal",
                    classification=FactClassification.FALSE_POSITIVE,
                    expectation=_signal_expect_text(forb),
                    actual=(
                        f"path={match.path!r} kind={match.signal_kind!r} "
                        f"level={match.confirmation_level!r}"
                    ),
                    diagnostic=forb.rationale or "forbidden AI Readiness signal present",
                    family_id=_normalize_family_id(forb.family_id) or forb.family_id,
                    path=match.path,
                )
            )

    for req in expectation.required_findings:
        matches = [item for item in actual if _finding_matches(req, item)]
        expected_count = req.expected_count if req.expected_count is not None else 1
        rule_id = req.rule_id or "ai_readiness.finding"
        if len(matches) >= expected_count:
            classifications.append(
                ClassifiedAiReadinessFact(
                    name=rule_id,
                    rule_id=rule_id,
                    classification=FactClassification.TRUE_POSITIVE,
                    expectation=_finding_expect_text(req),
                    actual=f"count={len(matches)}",
                    diagnostic=req.rationale or "required AI Readiness finding matched",
                    family_id=matches[0].family_id,
                    path=req.path or matches[0].path,
                )
            )
        else:
            classifications.append(
                ClassifiedAiReadinessFact(
                    name=rule_id,
                    rule_id=rule_id,
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=_finding_expect_text(req),
                    actual=f"count={len(matches)}",
                    diagnostic=req.rationale or "required AI Readiness finding missing",
                    path=req.path,
                )
            )

    for rule_id in expectation.expected_rule_ids:
        if rule_id in structured_required:
            continue
        present = [item for item in actual if item.rule_id == rule_id]
        if present:
            classifications.append(
                ClassifiedAiReadinessFact(
                    name=rule_id,
                    rule_id=rule_id,
                    classification=FactClassification.TRUE_POSITIVE,
                    expectation=f"required rule {rule_id}",
                    actual=f"count={len(present)}",
                    diagnostic="required rule present",
                    family_id=present[0].family_id,
                    path=present[0].path,
                )
            )
        else:
            classifications.append(
                ClassifiedAiReadinessFact(
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
                ClassifiedAiReadinessFact(
                    name=forb.rule_id or "ai_readiness.finding",
                    rule_id=forb.rule_id or "ai_readiness.finding",
                    classification=FactClassification.FALSE_POSITIVE,
                    expectation=_finding_expect_text(forb),
                    actual=f"path={match.path!r}",
                    diagnostic=forb.rationale or "forbidden AI Readiness finding present",
                    family_id=match.family_id,
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
                    ClassifiedAiReadinessFact(
                        name=rule_id,
                        rule_id=rule_id,
                        classification=FactClassification.AMBIGUOUS,
                        expectation="allowed overlap",
                        actual=f"path={match.path!r}",
                        diagnostic="allowed finding excluded from FP scoring",
                        family_id=match.family_id,
                        path=match.path,
                    )
                )
            else:
                classifications.append(
                    ClassifiedAiReadinessFact(
                        name=rule_id,
                        rule_id=rule_id,
                        classification=FactClassification.FALSE_POSITIVE,
                        expectation=f"forbidden rule {rule_id}",
                        actual=f"path={match.path!r}",
                        diagnostic="forbidden rule present",
                        family_id=match.family_id,
                        path=match.path,
                    )
                )

    for allowed in expectation.allowed_findings:
        matches = [item for item in actual if _finding_matches(allowed, item)]
        rule_id = allowed.rule_id or "ai_readiness.finding"
        if matches and rule_id not in structured_required:
            classifications.append(
                ClassifiedAiReadinessFact(
                    name=rule_id,
                    rule_id=rule_id,
                    classification=FactClassification.AMBIGUOUS,
                    expectation=allowed.rationale or "allowed finding",
                    actual=f"count={len(matches)}",
                    diagnostic="allowed finding not scored as TP",
                    family_id=matches[0].family_id,
                    path=allowed.path or matches[0].path,
                )
            )

    for req in expectation.required_recommendations:
        matches = [
            item for item in recommendations if _recommendation_matches(req, item)
        ]
        label = req.title_pattern or req.category or "recommendation"
        if matches:
            classifications.append(
                ClassifiedAiReadinessFact(
                    name=f"recommendation:{label}",
                    rule_id="ai_readiness.recommendation",
                    classification=FactClassification.TRUE_POSITIVE,
                    expectation=_recommendation_expect_text(req),
                    actual=f"title={matches[0].title!r}",
                    diagnostic=req.rationale or "required AI Readiness recommendation matched",
                )
            )
        else:
            classifications.append(
                ClassifiedAiReadinessFact(
                    name=f"recommendation:{label}",
                    rule_id="ai_readiness.recommendation",
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=_recommendation_expect_text(req),
                    actual="absent",
                    diagnostic=req.rationale or "required AI Readiness recommendation missing",
                )
            )

    for forb in expectation.forbidden_recommendations:
        matches = [
            item for item in recommendations if _recommendation_matches(forb, item)
        ]
        label = forb.title_pattern or forb.category or "recommendation"
        for match in matches:
            classifications.append(
                ClassifiedAiReadinessFact(
                    name=f"recommendation:{label}",
                    rule_id="ai_readiness.recommendation",
                    classification=FactClassification.FALSE_POSITIVE,
                    expectation=_recommendation_expect_text(forb),
                    actual=f"title={match.title!r}",
                    diagnostic=forb.rationale or "forbidden AI Readiness recommendation present",
                )
            )

    for range_spec in expectation.expected_count_ranges:
        count = sum(1 for item in actual if item.rule_id == range_spec.rule_id)
        if not range_spec.contains(count):
            classifications.append(
                ClassifiedAiReadinessFact(
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
                ClassifiedAiReadinessFact(
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
                ClassifiedAiReadinessFact(
                    name=rule_id,
                    rule_id=rule_id,
                    classification=FactClassification.NOT_APPLICABLE,
                    expectation="not applicable",
                    actual="absent",
                    diagnostic="rule marked not_applicable",
                )
            )

    parse_failures: list[str] = []
    limitation_blob = "\n".join(limitation_texts).lower()
    for expected_limit in expectation.expected_limitations:
        if expected_limit.lower() not in limitation_blob:
            parse_failures.append(f"expected_limitation_missing:{expected_limit}")

    if expectation.expected_coverage_state:
        observed = (coverage_state or "").strip().lower()
        expected_state = expectation.expected_coverage_state.strip().lower()
        if observed != expected_state and expected_state not in limitation_blob:
            artifact_blob = "\n".join((artifact_texts or {}).values()).lower()
            if expected_state not in artifact_blob and observed != expected_state:
                parse_failures.append(
                    f"expected_coverage_state_missing:{expectation.expected_coverage_state}"
                )

    path_failures: list[str] = []
    for item in actual:
        if item.path and (item.path.startswith("/") or item.path.startswith("\\")):
            path_failures.append(f"absolute_path:{item.rule_id}:{item.path}")
        if not item.evidence_ids:
            path_failures.append(f"missing_evidence:{item.rule_id}:{item.finding_id}")

    for item in signals:
        if item.path and (item.path.startswith("/") or item.path.startswith("\\")):
            path_failures.append(f"absolute_signal_path:{item.family_id}:{item.path}")

    unsupported: list[str] = []
    artifact_texts = artifact_texts or {}
    for claim in expectation.forbidden_conclusions:
        needle = claim.lower()
        for name, text in artifact_texts.items():
            lowered = text.lower()
            # Prefer word-boundary match so "ai ready" does not hit "ai readiness".
            if not _claim_present(lowered, needle):
                continue
            if not _is_disclaimer_negation(lowered, needle):
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
    per_family = _per_family_metrics(classifications)
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

    return AiReadinessValidationResult(
        repository_id=repository_id,
        classifications=tuple(classifications),
        per_rule_metrics=per_rule,
        per_family_metrics=per_family,
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


def aggregate_ai_readiness_results(
    results: list[AiReadinessValidationResult] | tuple[AiReadinessValidationResult, ...],
) -> AggregateAiReadinessMetrics:
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
    by_family: dict[str, list[int]] = {}
    for result in results_t:
        for metrics in result.per_rule_metrics:
            bucket = by_rule.setdefault(metrics.rule_id, [0, 0, 0, 0])
            bucket[0] += metrics.true_positives
            bucket[1] += metrics.false_positives
            bucket[2] += metrics.false_negatives
            bucket[3] += metrics.ambiguous
        for metrics in result.per_family_metrics:
            key = metrics.family_id or metrics.rule_id
            bucket = by_family.setdefault(key, [0, 0, 0, 0])
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
            AiReadinessRuleMetrics(
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
    per_family = []
    for family, (rtp, rfp, rfn, ramb) in sorted(by_family.items()):
        rprec, rrec, rreason = compute_precision_recall(
            true_positives=rtp, false_positives=rfp, false_negatives=rfn
        )
        per_family.append(
            AiReadinessRuleMetrics(
                rule_id=family,
                family_id=family,
                true_positives=rtp,
                false_positives=rfp,
                false_negatives=rfn,
                ambiguous=ramb,
                precision=rprec,
                recall=rrec,
                unavailable_reason=rreason,
            )
        )
    return AggregateAiReadinessMetrics(
        repository_count=len(results_t),
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        ambiguous=amb,
        precision=precision,
        recall=recall,
        per_rule=tuple(per_rule),
        per_family=tuple(per_family),
        per_repository=results_t,
    )


def _load_ai_readiness_evidence(
    artifact_paths: dict[str, str] | None,
) -> dict[str, Any] | None:
    if not artifact_paths:
        return None
    path_str = artifact_paths.get("repository-ai-readiness-evidence.json")
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


def _signal_kind_from_fact(family_id: str, fact: dict[str, Any]) -> str | None:
    del family_id  # AI Readiness facts use a uniform kind/detail shape.
    value = fact.get("kind") or fact.get("detail") or fact.get("system") or fact.get(
        "service"
    )
    if value is None or value == "":
        return None
    return str(value).lower()


def _signal_matches(
    expectation: AiReadinessSignalExpectation,
    actual: AiReadinessSignalActual,
) -> bool:
    if _norm(actual.family_id) != _norm(
        _normalize_family_id(expectation.family_id) or expectation.family_id
    ):
        return False
    if expectation.signal_kind and _norm(actual.signal_kind or "") != _norm(
        expectation.signal_kind
    ):
        return False
    if expectation.path and _norm_path(actual.path or "") != _norm_path(expectation.path):
        return False
    if expectation.path_pattern:
        if not actual.path or not re.search(expectation.path_pattern, actual.path):
            return False
    if expectation.signal_pattern:
        haystack = actual.signal_kind or actual.path or ""
        if not re.search(expectation.signal_pattern, haystack):
            return False
    return True


def _finding_matches(
    expectation: AiReadinessFindingExpectation,
    actual: AiReadinessFindingActual,
) -> bool:
    if expectation.rule_id and actual.rule_id != expectation.rule_id:
        return False
    if expectation.path and _norm_path(actual.path or "") != _norm_path(expectation.path):
        return False
    if expectation.path_pattern:
        if not actual.path or not re.search(expectation.path_pattern, actual.path):
            return False
    if expectation.severity and _norm(actual.severity or "") != _norm(expectation.severity):
        return False
    if expectation.confidence and _norm(actual.confidence or "") != _norm(
        expectation.confidence
    ):
        return False
    return True


def _recommendation_matches(
    expectation: AiReadinessRecommendationExpectation,
    actual: AiReadinessRecommendationActual,
) -> bool:
    if expectation.category and _norm(actual.category or "") != _norm(expectation.category):
        return False
    if expectation.title_pattern:
        if not re.search(expectation.title_pattern, actual.title, flags=re.IGNORECASE):
            return False
    elif not expectation.category and not expectation.supporting_rule_ids:
        return False
    if expectation.supporting_rule_ids:
        actual_rules = set(actual.supporting_rule_ids)
        if not all(rule_id in actual_rules for rule_id in expectation.supporting_rule_ids):
            return False
    return True


def _looks_like_ai_readiness_recommendation(item: dict[str, Any]) -> bool:
    haystacks = [
        str(item.get("category") or ""),
        str(item.get("presentation_group") or ""),
        str(item.get("kind") or ""),
        str(item.get("recommendation_id") or ""),
        str(item.get("id") or ""),
        str(item.get("title") or ""),
        " ".join(str(x) for x in (item.get("rule_ids") or [])),
    ]
    blob = " ".join(haystacks).lower()
    return "ai_readiness" in blob or "ai-readiness" in blob or "ai readiness" in blob


def _signal_expect_text(item: AiReadinessSignalExpectation) -> str:
    parts = [f"family={item.family_id}"]
    if item.signal_kind:
        parts.append(f"kind={item.signal_kind}")
    if item.path:
        parts.append(f"path={item.path}")
    if item.path_pattern:
        parts.append(f"path_pattern={item.path_pattern}")
    if item.signal_pattern:
        parts.append(f"signal_pattern={item.signal_pattern}")
    return ",".join(parts)


def _finding_expect_text(item: AiReadinessFindingExpectation) -> str:
    parts: list[str] = []
    if item.rule_id:
        parts.append(f"rule={item.rule_id}")
    if item.path:
        parts.append(f"path={item.path}")
    if item.path_pattern:
        parts.append(f"path_pattern={item.path_pattern}")
    if item.severity:
        parts.append(f"severity={item.severity}")
    return ",".join(parts) or "finding"


def _recommendation_expect_text(item: AiReadinessRecommendationExpectation) -> str:
    parts: list[str] = []
    if item.title_pattern:
        parts.append(f"title_pattern={item.title_pattern}")
    if item.category:
        parts.append(f"category={item.category}")
    if item.supporting_rule_ids:
        parts.append(f"rules={','.join(item.supporting_rule_ids)}")
    return ",".join(parts) or "recommendation"


def _per_rule_metrics(
    classifications: list[ClassifiedAiReadinessFact],
) -> tuple[AiReadinessRuleMetrics, ...]:
    rules = sorted({item.rule_id for item in classifications})
    metrics: list[AiReadinessRuleMetrics] = []
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
            AiReadinessRuleMetrics(
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


def _per_family_metrics(
    classifications: list[ClassifiedAiReadinessFact],
) -> tuple[AiReadinessRuleMetrics, ...]:
    families = sorted({item.family_id or "unknown" for item in classifications})
    metrics: list[AiReadinessRuleMetrics] = []
    for family_id in families:
        scoped = [
            item for item in classifications if (item.family_id or "unknown") == family_id
        ]
        tp = sum(1 for item in scoped if item.classification is FactClassification.TRUE_POSITIVE)
        fp = sum(1 for item in scoped if item.classification is FactClassification.FALSE_POSITIVE)
        fn = sum(1 for item in scoped if item.classification is FactClassification.FALSE_NEGATIVE)
        amb = sum(1 for item in scoped if item.classification is FactClassification.AMBIGUOUS)
        precision, recall, reason = compute_precision_recall(
            true_positives=tp, false_positives=fp, false_negatives=fn
        )
        metrics.append(
            AiReadinessRuleMetrics(
                rule_id=family_id,
                family_id=family_id,
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


def _claim_present(text: str, claim: str) -> bool:
    """True when ``claim`` appears as a phrase, not as a longer readiness stem."""

    pattern = rf"(?<![a-z0-9_]){re.escape(claim)}(?![a-z0-9_])"
    return re.search(pattern, text) is not None


def _is_disclaimer_negation(text: str, claim: str) -> bool:
    patterns = (
        rf"do not certify {re.escape(claim)}",
        rf"does not certify {re.escape(claim)}",
        rf"does not establish ai readiness",
        rf"do not establish ai readiness",
        rf"does not establish that the repository is ai ready",
        rf"were not assessed",
        rf"runtime model behavior",
        rf"organizational readiness",
        rf"absence of findings does not",
        rf"out of scope",
        rf"were not performed",
        rf"were not evaluated",
        rf"not performed",
        rf"zero evidence does not establish",
        rf"does not establish that ai readiness signals are absent",
        rf"repository-observable ai-enablement signals",
    )
    return any(re.search(pattern, text) for pattern in patterns)


def _normalize_family_id(value: Any) -> str | None:
    if value is None:
        return None
    raw = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    if not raw:
        return None
    if raw in _REPORT_FAMILY_ALIASES:
        return _REPORT_FAMILY_ALIASES[raw]
    if raw in AI_READINESS_FAMILIES:
        return raw
    return raw


def _norm(value: str) -> str:
    return value.strip().lower()


def _norm_path(value: str) -> str:
    # Strip only "./" prefixes — do not use lstrip("./"), which would mangle
    # paths like ".github/workflows/deploy.yml" into "github/...".
    normalized = value.replace("\\", "/").strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized
