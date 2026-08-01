"""Modernization authority-chain precision validation (Epic 4 Slice 4.10).

Validates the canonical deterministic chain in report.json:

Evidence → Finding → Recommendation → Priority Action → Roadmap Initiative

Uses ``assessment.deterministic_recommendations`` (preferred) else
``assessment.recommendations``, plus ``assessment.priority_actions`` and
``assessment.roadmap``. Pack-scoped recommendations are out of scope for the
primary chain (validated in pack slices); pack recommendation text is still
scanned via ``artifact_texts`` for forbidden conclusions.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from validation.inventory import (
    FactClassification,
    compute_precision_recall,
)

_PRESENTATION_FINDING_PREFIX = "presentation:finding:"

_FINDING_BACKED_TYPES = frozenset({"finding_backed", "merged"})

_ROADMAP_PHASES = frozenset({"stabilize", "secure", "modernize", "optimize"})

_ASSESSMENT_HEAD_ALIASES: dict[str, str] = {
    "security": "security",
    "security_intelligence": "security",
    "dependency": "dependency",
    "dependency_intelligence": "dependency",
    "architecture": "architecture",
    "architecture_intelligence": "architecture",
    "cloud": "cloud",
    "cloud_readiness": "cloud",
    "ai_readiness": "ai_readiness",
    "ai-readiness": "ai_readiness",
    "technical_debt": "technical_debt",
    "testing": "testing",
    "technology": "technology",
    "technology_inventory": "technology",
    "modernization": "modernization",
    "documentation": "documentation",
    "governance": "governance",
    "build": "build",
    "maintainability": "maintainability",
}


class ModernizationRecommendationExpectation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    category: str | None = None
    title_pattern: str | None = None
    intent: str | None = None  # free-text semantic intent for diagnostics
    supporting_rule_ids: tuple[str, ...] = ()
    expected_priority: str | None = None
    expected_count: int | None = Field(default=None, ge=0)
    assessment_head: str | None = None  # security|dependency|architecture|...
    rationale: str = ""


class ModernizationPriorityActionExpectation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    title_pattern: str | None = None
    supporting_recommendation_patterns: tuple[str, ...] = ()
    expected_priority: str | None = None
    expected_horizon: str | None = None  # immediate|near_term|future
    category: str | None = None
    rationale: str = ""


class ModernizationRoadmapInitiativeExpectation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    title_pattern: str | None = None
    phase: str | None = None  # stabilize|secure|modernize|optimize
    supporting_priority_action_patterns: tuple[str, ...] = ()
    initiative_type: str | None = None  # priority_action_backed|legacy|merged
    rationale: str = ""


class ModernizationCountRange(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    minimum: int | None = Field(default=None, ge=0)
    maximum: int | None = Field(default=None, ge=0)
    exact: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _validate_range(self) -> ModernizationCountRange:
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
        if not str(self.key or "").strip():
            raise ValueError("count range key must be non-empty")
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


class ModernizationExpectation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    required_recommendations: tuple[ModernizationRecommendationExpectation, ...] = ()
    forbidden_recommendations: tuple[ModernizationRecommendationExpectation, ...] = ()
    allowed_recommendations: tuple[ModernizationRecommendationExpectation, ...] = ()
    required_priority_actions: tuple[ModernizationPriorityActionExpectation, ...] = ()
    forbidden_priority_actions: tuple[ModernizationPriorityActionExpectation, ...] = ()
    required_roadmap_phases: tuple[str, ...] = ()
    forbidden_roadmap_phases: tuple[str, ...] = ()
    required_roadmap_initiatives: tuple[ModernizationRoadmapInitiativeExpectation, ...] = ()
    forbidden_roadmap_initiatives: tuple[ModernizationRoadmapInitiativeExpectation, ...] = ()
    expected_count_ranges: tuple[ModernizationCountRange, ...] = ()
    expected_limitations: tuple[str, ...] = ()
    maximum_false_positive_count: int | None = Field(default=None, ge=0)
    forbidden_conclusions: tuple[str, ...] = ()
    require_finding_backed_authority: bool = True
    require_priority_action_backed_roadmap: bool = True
    allow_legacy_recommendations: bool = True
    evidence_notes: str | None = None

    @model_validator(mode="after")
    def _reject_contradictions(self) -> ModernizationExpectation:
        required_titles = {
            item.title_pattern
            for item in self.required_recommendations
            if item.title_pattern
        }
        forbidden_titles = {
            item.title_pattern
            for item in self.forbidden_recommendations
            if item.title_pattern
        }
        title_overlap = sorted(required_titles & forbidden_titles)
        if title_overlap:
            raise ValueError(
                f"contradictory modernization recommendation title_pattern: {title_overlap}"
            )

        required_pa_titles = {
            item.title_pattern
            for item in self.required_priority_actions
            if item.title_pattern
        }
        forbidden_pa_titles = {
            item.title_pattern
            for item in self.forbidden_priority_actions
            if item.title_pattern
        }
        pa_overlap = sorted(required_pa_titles & forbidden_pa_titles)
        if pa_overlap:
            raise ValueError(
                f"contradictory modernization priority action title_pattern: {pa_overlap}"
            )

        required_phases = {_norm_phase(item) for item in self.required_roadmap_phases}
        forbidden_phases = {_norm_phase(item) for item in self.forbidden_roadmap_phases}
        phase_overlap = sorted(required_phases & forbidden_phases)
        if phase_overlap:
            raise ValueError(
                f"contradictory modernization roadmap phases: {phase_overlap}"
            )

        required_init_titles = {
            item.title_pattern
            for item in self.required_roadmap_initiatives
            if item.title_pattern
        }
        forbidden_init_titles = {
            item.title_pattern
            for item in self.forbidden_roadmap_initiatives
            if item.title_pattern
        }
        init_overlap = sorted(required_init_titles & forbidden_init_titles)
        if init_overlap:
            raise ValueError(
                "contradictory modernization roadmap initiative "
                f"title_pattern: {init_overlap}"
            )
        return self


class ModernizationRecommendationActual(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    recommendation_id: str | None = None
    title: str
    category: str | None = None
    priority: str | None = None
    recommendation_type: str | None = None
    primary_finding_id: str | None = None
    supporting_finding_ids: tuple[str, ...] = ()
    related_finding_ids: tuple[str, ...] = ()
    supporting_rule_ids: tuple[str, ...] = ()
    evidence_completeness: str | None = None
    assessment_head: str | None = None
    summary: str | None = None


class ModernizationPriorityActionActual(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    action_id: str | None = None
    title: str
    priority: str | None = None
    presentation_bucket: str | None = None
    category: str | None = None
    primary_recommendation_id: str | None = None
    supporting_recommendation_ids: tuple[str, ...] = ()
    supporting_finding_ids: tuple[str, ...] = ()
    summary: str | None = None


class ModernizationRoadmapInitiativeActual(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    initiative_id: str | None = None
    title: str
    phase: str | None = None
    initiative_type: str | None = None
    primary_priority_action_id: str | None = None
    supporting_priority_action_ids: tuple[str, ...] = ()
    supporting_recommendation_ids: tuple[str, ...] = ()
    supporting_finding_ids: tuple[str, ...] = ()


class ClassifiedModernizationFact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    rule_id: str
    classification: FactClassification
    expectation: str
    actual: str
    diagnostic: str
    category: str | None = None
    priority: str | None = None
    assessment_head: str | None = None


class ModernizationRuleMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    ambiguous: int = 0
    precision: float | None = None
    recall: float | None = None
    unavailable_reason: str | None = None


class ModernizationValidationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    repository_id: str
    classifications: tuple[ClassifiedModernizationFact, ...] = ()
    per_category_metrics: tuple[ModernizationRuleMetrics, ...] = ()
    per_priority_metrics: tuple[ModernizationRuleMetrics, ...] = ()
    per_assessment_head_metrics: tuple[ModernizationRuleMetrics, ...] = ()
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    ambiguous: int = 0
    precision: float | None = None
    recall: float | None = None
    unsupported_claim_failures: tuple[str, ...] = ()
    parse_coverage_failures: tuple[str, ...] = ()
    passed: bool = True
    diagnostics: tuple[str, ...] = ()


class AggregateModernizationMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    repository_count: int = 0
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    ambiguous: int = 0
    precision: float | None = None
    recall: float | None = None
    per_category: tuple[ModernizationRuleMetrics, ...] = ()
    per_priority: tuple[ModernizationRuleMetrics, ...] = ()
    per_assessment_head: tuple[ModernizationRuleMetrics, ...] = ()
    per_repository: tuple[ModernizationValidationResult, ...] = ()


def build_modernization_finding_index(
    document: dict[str, Any],
) -> dict[str, str]:
    """Build finding id → rule_id index from assessment.findings."""

    assessment = document.get("assessment") if isinstance(document.get("assessment"), dict) else {}
    findings = assessment.get("findings") or document.get("findings") or []
    index: dict[str, str] = {}
    if not isinstance(findings, list):
        return index
    for item in findings:
        if not isinstance(item, dict):
            continue
        finding_id = item.get("id")
        rule_id = item.get("rule_id")
        if finding_id and rule_id:
            index[str(finding_id)] = str(rule_id)
    return index


def extract_modernization_recommendations(
    document: dict[str, Any],
    finding_index: dict[str, str] | None = None,
) -> tuple[ModernizationRecommendationActual, ...]:
    """Extract canonical deterministic recommendations from report.json."""

    assessment = document.get("assessment") if isinstance(document.get("assessment"), dict) else {}
    raw = assessment.get("deterministic_recommendations")
    if not isinstance(raw, list):
        raw = assessment.get("recommendations")
    if not isinstance(raw, list):
        raw = document.get("recommendations")
    if not isinstance(raw, list):
        return ()

    index = finding_index if finding_index is not None else build_modernization_finding_index(document)
    rows: list[ModernizationRecommendationActual] = []
    seen: set[tuple[str, str | None]] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        title = item.get("title") or item.get("action")
        if not title:
            continue
        rec_id = item.get("id") or item.get("recommendation_id")
        key = (str(title), str(rec_id) if rec_id else None)
        if key in seen:
            continue
        seen.add(key)

        supporting_finding_ids = _string_id_tuple(
            item.get("supporting_finding_ids") or item.get("related_finding_ids") or []
        )
        related_finding_ids = _string_id_tuple(
            item.get("related_finding_ids") or item.get("supporting_finding_ids") or []
        )
        primary = item.get("primary_finding_id")
        primary_finding_id = str(primary) if primary else None

        rule_ids_raw = item.get("supporting_rule_ids") or item.get("rule_ids") or []
        supporting_rules = [
            str(rule_id)
            for rule_id in rule_ids_raw
            if isinstance(rule_id, str) and rule_id.strip()
        ]
        if not supporting_rules:
            for fid in supporting_finding_ids or related_finding_ids:
                rule_id = index.get(fid)
                if rule_id:
                    supporting_rules.append(rule_id)
        # Also accept a direct rule_id field on the recommendation payload.
        if item.get("rule_id") and str(item["rule_id"]) not in supporting_rules:
            # Prefer finding-derived rules when present; keep explicit rule_id as fallback.
            if not supporting_rules:
                supporting_rules.append(str(item["rule_id"]))

        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        category = (
            item.get("category")
            or item.get("presentation_group")
            or item.get("dimension")
            or metadata.get("category")
        )
        assessment_head = _derive_assessment_head(
            category=str(category) if category else None,
            metadata=metadata,
            item=item,
        )
        summary = item.get("summary") or item.get("description")
        rows.append(
            ModernizationRecommendationActual(
                recommendation_id=str(rec_id) if rec_id else None,
                title=str(title),
                category=str(category) if category else None,
                priority=str(item["priority"]).lower() if item.get("priority") else None,
                recommendation_type=(
                    str(item["recommendation_type"]).lower()
                    if item.get("recommendation_type")
                    else None
                ),
                primary_finding_id=primary_finding_id,
                supporting_finding_ids=supporting_finding_ids,
                related_finding_ids=related_finding_ids,
                supporting_rule_ids=tuple(sorted(set(supporting_rules))),
                evidence_completeness=(
                    str(item["evidence_completeness"]).lower()
                    if item.get("evidence_completeness")
                    else None
                ),
                assessment_head=assessment_head,
                summary=str(summary) if summary else None,
            )
        )
    return tuple(rows)


def extract_modernization_priority_actions(
    document: dict[str, Any],
) -> tuple[ModernizationPriorityActionActual, ...]:
    """Extract assessment.priority_actions from report.json."""

    assessment = document.get("assessment") if isinstance(document.get("assessment"), dict) else {}
    raw = assessment.get("priority_actions") or document.get("priority_actions") or []
    if not isinstance(raw, list):
        return ()

    rows: list[ModernizationPriorityActionActual] = []
    seen: set[tuple[str, str | None]] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        title = item.get("title") or item.get("action")
        if not title:
            continue
        action_id = item.get("action_id") or item.get("id")
        key = (str(title), str(action_id) if action_id else None)
        if key in seen:
            continue
        seen.add(key)
        primary = item.get("primary_recommendation_id")
        summary = item.get("summary") or item.get("description") or item.get("rationale")
        rows.append(
            ModernizationPriorityActionActual(
                action_id=str(action_id) if action_id else None,
                title=str(title),
                priority=str(item["priority"]).lower() if item.get("priority") else None,
                presentation_bucket=(
                    str(item["presentation_bucket"]).lower()
                    if item.get("presentation_bucket")
                    else None
                ),
                category=str(item["category"]) if item.get("category") else None,
                primary_recommendation_id=str(primary) if primary else None,
                supporting_recommendation_ids=_string_id_tuple(
                    item.get("supporting_recommendation_ids") or []
                ),
                supporting_finding_ids=_string_id_tuple(
                    item.get("supporting_finding_ids") or []
                ),
                summary=str(summary) if summary else None,
            )
        )
    return tuple(rows)


def extract_modernization_roadmap_initiatives(
    document: dict[str, Any],
) -> tuple[ModernizationRoadmapInitiativeActual, ...]:
    """Flatten roadmap phases[].initiatives or roadmap.initiatives."""

    assessment = document.get("assessment") if isinstance(document.get("assessment"), dict) else {}
    roadmap = assessment.get("roadmap") if isinstance(assessment.get("roadmap"), dict) else {}
    if not roadmap and isinstance(document.get("roadmap"), dict):
        roadmap = document["roadmap"]

    rows: list[ModernizationRoadmapInitiativeActual] = []
    seen: set[tuple[str, str | None]] = set()

    def _consume(items: Any, *, default_phase: str | None = None) -> None:
        if not isinstance(items, list):
            return
        for item in items:
            if not isinstance(item, dict):
                continue
            title = item.get("title") or item.get("summary")
            if not title:
                continue
            initiative_id = item.get("initiative_id") or item.get("id")
            key = (str(title), str(initiative_id) if initiative_id else None)
            if key in seen:
                continue
            seen.add(key)
            phase_raw = item.get("phase") or default_phase
            primary = item.get("primary_priority_action_id")
            rows.append(
                ModernizationRoadmapInitiativeActual(
                    initiative_id=str(initiative_id) if initiative_id else None,
                    title=str(title),
                    phase=_norm_phase(phase_raw) if phase_raw else None,
                    initiative_type=(
                        str(item["initiative_type"]).lower()
                        if item.get("initiative_type")
                        else None
                    ),
                    primary_priority_action_id=str(primary) if primary else None,
                    supporting_priority_action_ids=_string_id_tuple(
                        item.get("supporting_priority_action_ids") or []
                    ),
                    supporting_recommendation_ids=_string_id_tuple(
                        item.get("supporting_recommendation_ids") or []
                    ),
                    supporting_finding_ids=_string_id_tuple(
                        item.get("supporting_finding_ids") or []
                    ),
                )
            )

    phases = roadmap.get("phases") or []
    if isinstance(phases, list):
        for phase in phases:
            if not isinstance(phase, dict):
                continue
            phase_name = phase.get("phase") or phase.get("id") or phase.get("name")
            _consume(phase.get("initiatives"), default_phase=str(phase_name) if phase_name else None)
    _consume(roadmap.get("initiatives"))
    return tuple(rows)


def extract_modernization_roadmap_phases(
    document: dict[str, Any],
) -> tuple[str, ...]:
    """Return normalized roadmap phase names present in the report."""

    assessment = document.get("assessment") if isinstance(document.get("assessment"), dict) else {}
    roadmap = assessment.get("roadmap") if isinstance(assessment.get("roadmap"), dict) else {}
    if not roadmap and isinstance(document.get("roadmap"), dict):
        roadmap = document["roadmap"]

    phases: set[str] = set()
    for phase in roadmap.get("phases") or []:
        if not isinstance(phase, dict):
            continue
        raw = phase.get("phase") or phase.get("id") or phase.get("name")
        if raw:
            phases.add(_norm_phase(raw))
    for initiative in extract_modernization_roadmap_initiatives(document):
        if initiative.phase:
            phases.add(_norm_phase(initiative.phase))
    return tuple(sorted(phases))


def validate_modernization_precision(
    *,
    repository_id: str,
    expectation: ModernizationExpectation,
    actual_recommendations: (
        tuple[ModernizationRecommendationActual, ...] | list[ModernizationRecommendationActual]
    ),
    actual_priority_actions: (
        tuple[ModernizationPriorityActionActual, ...] | list[ModernizationPriorityActionActual]
    ) = (),
    actual_roadmap_initiatives: (
        tuple[ModernizationRoadmapInitiativeActual, ...] | list[ModernizationRoadmapInitiativeActual]
    ) = (),
    finding_ids: set[str] | frozenset[str] | tuple[str, ...] | list[str] | None = None,
    recommendation_ids: set[str] | frozenset[str] | tuple[str, ...] | list[str] | None = None,
    artifact_texts: dict[str, str] | None = None,
    limitation_texts: tuple[str, ...] | list[str] = (),
    ai_executed: bool = False,
    roadmap_phases: tuple[str, ...] | list[str] | None = None,
) -> ModernizationValidationResult:
    recommendations = tuple(actual_recommendations)
    priority_actions = tuple(actual_priority_actions)
    initiatives = tuple(actual_roadmap_initiatives)
    finding_id_set = {str(item) for item in (finding_ids or []) if item}
    recommendation_id_set = {str(item) for item in (recommendation_ids or []) if item}
    if not recommendation_id_set:
        recommendation_id_set = {
            item.recommendation_id
            for item in recommendations
            if item.recommendation_id
        }
    recommendations_by_id = {
        item.recommendation_id: item
        for item in recommendations
        if item.recommendation_id
    }
    priority_actions_by_id = {
        item.action_id: item for item in priority_actions if item.action_id
    }
    observed_phases = {
        _norm_phase(item)
        for item in (roadmap_phases or [])
        if item
    } | {
        _norm_phase(item.phase)
        for item in initiatives
        if item.phase
    }

    classifications: list[ClassifiedModernizationFact] = []

    if ai_executed:
        classifications.append(
            ClassifiedModernizationFact(
                name="ai_executed",
                rule_id="modernization.ai_guard",
                classification=FactClassification.FALSE_POSITIVE,
                expectation="ai_executed=false",
                actual="ai_executed=true",
                diagnostic="AI must be disabled for modernization validation",
            )
        )

    for req in expectation.required_recommendations:
        matches = [
            item for item in recommendations if _recommendation_matches(req, item)
        ]
        expected_count = req.expected_count if req.expected_count is not None else 1
        label = req.title_pattern or req.category or req.intent or "recommendation"
        if len(matches) >= expected_count:
            match = matches[0]
            classifications.append(
                ClassifiedModernizationFact(
                    name=f"recommendation:{label}",
                    rule_id="modernization.recommendation",
                    classification=FactClassification.TRUE_POSITIVE,
                    expectation=_recommendation_expect_text(req),
                    actual=f"title={match.title!r} count={len(matches)}",
                    diagnostic=req.rationale or "required modernization recommendation matched",
                    category=match.category or req.category,
                    priority=match.priority or req.expected_priority,
                    assessment_head=match.assessment_head or req.assessment_head,
                )
            )
        else:
            classifications.append(
                ClassifiedModernizationFact(
                    name=f"recommendation:{label}",
                    rule_id="modernization.recommendation",
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=_recommendation_expect_text(req),
                    actual=f"count={len(matches)}",
                    diagnostic=req.rationale or "required modernization recommendation missing",
                    category=req.category,
                    priority=req.expected_priority,
                    assessment_head=req.assessment_head,
                )
            )

    for forb in expectation.forbidden_recommendations:
        matches = [
            item for item in recommendations if _recommendation_matches(forb, item)
        ]
        label = forb.title_pattern or forb.category or forb.intent or "recommendation"
        for match in matches:
            if any(
                _recommendation_matches(allowed, match)
                for allowed in expectation.allowed_recommendations
            ):
                classifications.append(
                    ClassifiedModernizationFact(
                        name=f"recommendation:{label}",
                        rule_id="modernization.recommendation",
                        classification=FactClassification.AMBIGUOUS,
                        expectation=_recommendation_expect_text(forb),
                        actual=f"title={match.title!r}",
                        diagnostic="allowed recommendation excluded from FP scoring",
                        category=match.category,
                        priority=match.priority,
                        assessment_head=match.assessment_head,
                    )
                )
            else:
                classifications.append(
                    ClassifiedModernizationFact(
                        name=f"recommendation:{label}",
                        rule_id="modernization.recommendation",
                        classification=FactClassification.FALSE_POSITIVE,
                        expectation=_recommendation_expect_text(forb),
                        actual=f"title={match.title!r}",
                        diagnostic=(
                            forb.rationale or "forbidden modernization recommendation present"
                        ),
                        category=match.category,
                        priority=match.priority,
                        assessment_head=match.assessment_head,
                    )
                )

    required_rec_keys = {
        _recommendation_expect_text(item) for item in expectation.required_recommendations
    }
    for allowed in expectation.allowed_recommendations:
        matches = [
            item for item in recommendations if _recommendation_matches(allowed, item)
        ]
        label = allowed.title_pattern or allowed.category or allowed.intent or "recommendation"
        if matches and _recommendation_expect_text(allowed) not in required_rec_keys:
            match = matches[0]
            classifications.append(
                ClassifiedModernizationFact(
                    name=f"recommendation:{label}",
                    rule_id="modernization.recommendation",
                    classification=FactClassification.AMBIGUOUS,
                    expectation=allowed.rationale or "allowed recommendation",
                    actual=f"title={match.title!r} count={len(matches)}",
                    diagnostic="allowed recommendation not scored as TP",
                    category=match.category or allowed.category,
                    priority=match.priority or allowed.expected_priority,
                    assessment_head=match.assessment_head or allowed.assessment_head,
                )
            )

    for req in expectation.required_priority_actions:
        matches = [
            item
            for item in priority_actions
            if _priority_action_matches(req, item, recommendations_by_id)
        ]
        label = req.title_pattern or req.category or "priority_action"
        if matches:
            match = matches[0]
            classifications.append(
                ClassifiedModernizationFact(
                    name=f"priority_action:{label}",
                    rule_id="modernization.priority_action",
                    classification=FactClassification.TRUE_POSITIVE,
                    expectation=_priority_action_expect_text(req),
                    actual=f"title={match.title!r}",
                    diagnostic=req.rationale or "required priority action matched",
                    category=match.category or req.category,
                    priority=match.priority or req.expected_priority,
                )
            )
        else:
            classifications.append(
                ClassifiedModernizationFact(
                    name=f"priority_action:{label}",
                    rule_id="modernization.priority_action",
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=_priority_action_expect_text(req),
                    actual="absent",
                    diagnostic=req.rationale or "required priority action missing",
                    category=req.category,
                    priority=req.expected_priority,
                )
            )

    for forb in expectation.forbidden_priority_actions:
        matches = [
            item
            for item in priority_actions
            if _priority_action_matches(forb, item, recommendations_by_id)
        ]
        label = forb.title_pattern or forb.category or "priority_action"
        for match in matches:
            classifications.append(
                ClassifiedModernizationFact(
                    name=f"priority_action:{label}",
                    rule_id="modernization.priority_action",
                    classification=FactClassification.FALSE_POSITIVE,
                    expectation=_priority_action_expect_text(forb),
                    actual=f"title={match.title!r}",
                    diagnostic=forb.rationale or "forbidden priority action present",
                    category=match.category,
                    priority=match.priority,
                )
            )

    for phase in expectation.required_roadmap_phases:
        normalized = _norm_phase(phase)
        if normalized in observed_phases:
            classifications.append(
                ClassifiedModernizationFact(
                    name=f"roadmap_phase:{normalized}",
                    rule_id="modernization.roadmap_phase",
                    classification=FactClassification.TRUE_POSITIVE,
                    expectation=f"required phase {normalized}",
                    actual="present",
                    diagnostic="required roadmap phase present",
                )
            )
        else:
            classifications.append(
                ClassifiedModernizationFact(
                    name=f"roadmap_phase:{normalized}",
                    rule_id="modernization.roadmap_phase",
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=f"required phase {normalized}",
                    actual="absent",
                    diagnostic="required roadmap phase missing",
                )
            )

    for phase in expectation.forbidden_roadmap_phases:
        normalized = _norm_phase(phase)
        if normalized in observed_phases:
            classifications.append(
                ClassifiedModernizationFact(
                    name=f"roadmap_phase:{normalized}",
                    rule_id="modernization.roadmap_phase",
                    classification=FactClassification.FALSE_POSITIVE,
                    expectation=f"forbidden phase {normalized}",
                    actual="present",
                    diagnostic="forbidden roadmap phase present",
                )
            )

    for req in expectation.required_roadmap_initiatives:
        matches = [
            item
            for item in initiatives
            if _initiative_matches(req, item, priority_actions_by_id)
        ]
        label = req.title_pattern or req.phase or req.initiative_type or "initiative"
        if matches:
            match = matches[0]
            classifications.append(
                ClassifiedModernizationFact(
                    name=f"roadmap_initiative:{label}",
                    rule_id="modernization.roadmap_initiative",
                    classification=FactClassification.TRUE_POSITIVE,
                    expectation=_initiative_expect_text(req),
                    actual=f"title={match.title!r} phase={match.phase!r}",
                    diagnostic=req.rationale or "required roadmap initiative matched",
                    category=match.phase,
                )
            )
        else:
            classifications.append(
                ClassifiedModernizationFact(
                    name=f"roadmap_initiative:{label}",
                    rule_id="modernization.roadmap_initiative",
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=_initiative_expect_text(req),
                    actual="absent",
                    diagnostic=req.rationale or "required roadmap initiative missing",
                    category=req.phase,
                )
            )

    for forb in expectation.forbidden_roadmap_initiatives:
        matches = [
            item
            for item in initiatives
            if _initiative_matches(forb, item, priority_actions_by_id)
        ]
        label = forb.title_pattern or forb.phase or forb.initiative_type or "initiative"
        for match in matches:
            classifications.append(
                ClassifiedModernizationFact(
                    name=f"roadmap_initiative:{label}",
                    rule_id="modernization.roadmap_initiative",
                    classification=FactClassification.FALSE_POSITIVE,
                    expectation=_initiative_expect_text(forb),
                    actual=f"title={match.title!r} phase={match.phase!r}",
                    diagnostic=forb.rationale or "forbidden roadmap initiative present",
                    category=match.phase,
                )
            )

    for range_spec in expectation.expected_count_ranges:
        count = _count_for_key(
            range_spec.key,
            recommendations=recommendations,
            priority_actions=priority_actions,
            initiatives=initiatives,
        )
        if not range_spec.contains(count):
            classifications.append(
                ClassifiedModernizationFact(
                    name=range_spec.key,
                    rule_id=range_spec.key,
                    classification=FactClassification.FALSE_NEGATIVE,
                    expectation=f"count {range_spec.describe()}",
                    actual=f"count={count}",
                    diagnostic="modernization count outside range",
                )
            )

    if expectation.require_finding_backed_authority:
        classifications.extend(
            _structural_recommendation_checks(
                recommendations,
                finding_ids=finding_id_set,
                allow_legacy=expectation.allow_legacy_recommendations,
            )
        )
        classifications.extend(
            _structural_priority_action_checks(
                priority_actions,
                recommendation_ids=recommendation_id_set,
                require_finding_backed=True,
            )
        )
        classifications.extend(
            _priority_action_legacy_recommendation_checks(
                priority_actions,
                recommendations_by_id=recommendations_by_id,
            )
        )

    if expectation.require_priority_action_backed_roadmap:
        classifications.extend(
            _structural_roadmap_checks(
                initiatives,
                priority_actions_by_id=priority_actions_by_id,
                require_pa_backed=True,
            )
        )

    parse_failures: list[str] = []
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
            if not _claim_present(lowered, needle):
                continue
            if not _is_disclaimer_negation(lowered, needle):
                unsupported.append(f"{name}:{claim}")

    tp = sum(
        1 for item in classifications if item.classification is FactClassification.TRUE_POSITIVE
    )
    fp = sum(
        1 for item in classifications if item.classification is FactClassification.FALSE_POSITIVE
    )
    fn = sum(
        1 for item in classifications if item.classification is FactClassification.FALSE_NEGATIVE
    )
    amb = sum(
        1 for item in classifications if item.classification is FactClassification.AMBIGUOUS
    )
    precision, recall, _ = compute_precision_recall(
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
    )
    per_category = _metrics_by_attr(classifications, attr="category")
    per_priority = _metrics_by_attr(classifications, attr="priority")
    per_assessment_head = _metrics_by_attr(classifications, attr="assessment_head")

    diagnostics = [
        f"{item.classification.value}:{item.rule_id}:{item.diagnostic}"
        for item in classifications
        if item.classification
        in {FactClassification.FALSE_POSITIVE, FactClassification.FALSE_NEGATIVE}
    ]
    diagnostics.extend(f"unsupported:{item}" for item in unsupported)
    diagnostics.extend(f"parse:{item}" for item in parse_failures)

    passed = fp == 0 and fn == 0 and not unsupported and not parse_failures
    if expectation.maximum_false_positive_count is not None:
        passed = (
            fn == 0
            and not unsupported
            and not parse_failures
            and fp <= expectation.maximum_false_positive_count
        )

    return ModernizationValidationResult(
        repository_id=repository_id,
        classifications=tuple(classifications),
        per_category_metrics=per_category,
        per_priority_metrics=per_priority,
        per_assessment_head_metrics=per_assessment_head,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        ambiguous=amb,
        precision=precision,
        recall=recall,
        unsupported_claim_failures=tuple(unsupported),
        parse_coverage_failures=tuple(parse_failures),
        passed=passed,
        diagnostics=tuple(diagnostics),
    )


def aggregate_modernization_results(
    results: list[ModernizationValidationResult] | tuple[ModernizationValidationResult, ...],
) -> AggregateModernizationMetrics:
    results_t = tuple(sorted(results, key=lambda item: item.repository_id))
    tp = sum(item.true_positives for item in results_t)
    fp = sum(item.false_positives for item in results_t)
    fn = sum(item.false_negatives for item in results_t)
    amb = sum(item.ambiguous for item in results_t)
    precision, recall, _ = compute_precision_recall(
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
    )

    def _merge(
        getters: list[tuple[ModernizationRuleMetrics, ...]],
    ) -> tuple[ModernizationRuleMetrics, ...]:
        by_key: dict[str, list[int]] = {}
        for metrics_tuple in getters:
            for metrics in metrics_tuple:
                bucket = by_key.setdefault(metrics.rule_id, [0, 0, 0, 0])
                bucket[0] += metrics.true_positives
                bucket[1] += metrics.false_positives
                bucket[2] += metrics.false_negatives
                bucket[3] += metrics.ambiguous
        merged: list[ModernizationRuleMetrics] = []
        for rule_id, (rtp, rfp, rfn, ramb) in sorted(by_key.items()):
            rprec, rrec, rreason = compute_precision_recall(
                true_positives=rtp, false_positives=rfp, false_negatives=rfn
            )
            merged.append(
                ModernizationRuleMetrics(
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
        return tuple(merged)

    return AggregateModernizationMetrics(
        repository_count=len(results_t),
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        ambiguous=amb,
        precision=precision,
        recall=recall,
        per_category=_merge([item.per_category_metrics for item in results_t]),
        per_priority=_merge([item.per_priority_metrics for item in results_t]),
        per_assessment_head=_merge(
            [item.per_assessment_head_metrics for item in results_t]
        ),
        per_repository=results_t,
    )


def _structural_recommendation_checks(
    recommendations: tuple[ModernizationRecommendationActual, ...],
    *,
    finding_ids: set[str],
    allow_legacy: bool,
) -> list[ClassifiedModernizationFact]:
    out: list[ClassifiedModernizationFact] = []
    for item in recommendations:
        rec_label = item.recommendation_id or item.title
        if not _requires_finding_authority(item):
            if _is_legacy_recommendation(item):
                if allow_legacy:
                    continue
                out.append(
                    ClassifiedModernizationFact(
                        name=f"recommendation_authority:{rec_label}",
                        rule_id="modernization.authority",
                        classification=FactClassification.FALSE_POSITIVE,
                        expectation="finding-backed recommendation",
                        actual=(
                            f"type={item.recommendation_type!r} "
                            f"supporting={list(item.supporting_finding_ids)!r}"
                        ),
                        diagnostic="legacy recommendation not allowed",
                        category=item.category,
                        priority=item.priority,
                        assessment_head=item.assessment_head,
                    )
                )
            continue

        if not item.supporting_finding_ids:
            out.append(
                ClassifiedModernizationFact(
                    name=f"recommendation_authority:{rec_label}",
                    rule_id="modernization.authority",
                    classification=FactClassification.FALSE_POSITIVE,
                    expectation="supporting_finding_ids non-empty",
                    actual="supporting_finding_ids=[]",
                    diagnostic="finding-backed recommendation missing supporting findings",
                    category=item.category,
                    priority=item.priority,
                    assessment_head=item.assessment_head,
                )
            )
            continue
        if (
            item.primary_finding_id
            and item.primary_finding_id not in item.supporting_finding_ids
        ):
            out.append(
                ClassifiedModernizationFact(
                    name=f"recommendation_authority:{rec_label}",
                    rule_id="modernization.authority",
                    classification=FactClassification.FALSE_POSITIVE,
                    expectation="primary_finding_id in supporting_finding_ids",
                    actual=(
                        f"primary={item.primary_finding_id!r} "
                        f"supporting={list(item.supporting_finding_ids)!r}"
                    ),
                    diagnostic="primary_finding_id not in supporting_finding_ids",
                    category=item.category,
                    priority=item.priority,
                    assessment_head=item.assessment_head,
                )
            )
        if (
            item.related_finding_ids
            and item.supporting_finding_ids
            and set(item.related_finding_ids) != set(item.supporting_finding_ids)
        ):
            out.append(
                ClassifiedModernizationFact(
                    name=f"recommendation_authority:{rec_label}",
                    rule_id="modernization.authority",
                    classification=FactClassification.FALSE_POSITIVE,
                    expectation="related_finding_ids == supporting_finding_ids",
                    actual=(
                        f"related={list(item.related_finding_ids)!r} "
                        f"supporting={list(item.supporting_finding_ids)!r}"
                    ),
                    diagnostic="related_finding_ids diverge from supporting_finding_ids",
                    category=item.category,
                    priority=item.priority,
                    assessment_head=item.assessment_head,
                )
            )
        for fid in item.supporting_finding_ids:
            if finding_ids and fid not in finding_ids:
                out.append(
                    ClassifiedModernizationFact(
                        name=f"recommendation_authority:{rec_label}",
                        rule_id="modernization.authority",
                        classification=FactClassification.FALSE_POSITIVE,
                        expectation="supporting finding ids exist",
                        actual=f"missing_finding_id={fid!r}",
                        diagnostic="supporting finding id not present in findings",
                        category=item.category,
                        priority=item.priority,
                        assessment_head=item.assessment_head,
                    )
                )
            if fid.startswith(_PRESENTATION_FINDING_PREFIX):
                out.append(
                    ClassifiedModernizationFact(
                        name=f"recommendation_authority:{rec_label}",
                        rule_id="modernization.authority",
                        classification=FactClassification.FALSE_POSITIVE,
                        expectation="no presentation:finding: ids",
                        actual=f"finding_id={fid!r}",
                        diagnostic="presentation:finding: id in recommendation chain",
                        category=item.category,
                        priority=item.priority,
                        assessment_head=item.assessment_head,
                    )
                )
        if item.recommendation_id and item.recommendation_id.startswith(
            _PRESENTATION_FINDING_PREFIX
        ):
            out.append(
                ClassifiedModernizationFact(
                    name=f"recommendation_authority:{rec_label}",
                    rule_id="modernization.authority",
                    classification=FactClassification.FALSE_POSITIVE,
                    expectation="no presentation:finding: ids",
                    actual=f"recommendation_id={item.recommendation_id!r}",
                    diagnostic="presentation:finding: id in recommendation chain",
                    category=item.category,
                    priority=item.priority,
                    assessment_head=item.assessment_head,
                )
            )
    return out


def _structural_priority_action_checks(
    priority_actions: tuple[ModernizationPriorityActionActual, ...],
    *,
    recommendation_ids: set[str],
    require_finding_backed: bool,
) -> list[ClassifiedModernizationFact]:
    out: list[ClassifiedModernizationFact] = []
    for item in priority_actions:
        label = item.action_id or item.title
        if item.action_id and item.action_id.startswith(_PRESENTATION_FINDING_PREFIX):
            out.append(
                ClassifiedModernizationFact(
                    name=f"priority_action_authority:{label}",
                    rule_id="modernization.authority",
                    classification=FactClassification.FALSE_POSITIVE,
                    expectation="no presentation:finding: action_id",
                    actual=f"action_id={item.action_id!r}",
                    diagnostic="presentation:finding: id in priority action chain",
                    category=item.category,
                    priority=item.priority,
                )
            )
        if not item.supporting_recommendation_ids:
            out.append(
                ClassifiedModernizationFact(
                    name=f"priority_action_authority:{label}",
                    rule_id="modernization.authority",
                    classification=FactClassification.FALSE_POSITIVE,
                    expectation="supporting_recommendation_ids non-empty",
                    actual="supporting_recommendation_ids=[]",
                    diagnostic="priority action missing supporting recommendations",
                    category=item.category,
                    priority=item.priority,
                )
            )
        if item.primary_recommendation_id:
            primary = item.primary_recommendation_id
            if (
                primary not in item.supporting_recommendation_ids
                and primary not in recommendation_ids
            ):
                out.append(
                    ClassifiedModernizationFact(
                        name=f"priority_action_authority:{label}",
                        rule_id="modernization.authority",
                        classification=FactClassification.FALSE_POSITIVE,
                        expectation="primary_recommendation_id resolves",
                        actual=f"primary={primary!r}",
                        diagnostic="primary_recommendation_id does not resolve",
                        category=item.category,
                        priority=item.priority,
                    )
                )
        if require_finding_backed and not item.supporting_finding_ids:
            out.append(
                ClassifiedModernizationFact(
                    name=f"priority_action_authority:{label}",
                    rule_id="modernization.authority",
                    classification=FactClassification.FALSE_POSITIVE,
                    expectation="supporting_finding_ids non-empty",
                    actual="supporting_finding_ids=[]",
                    diagnostic="priority action missing supporting findings",
                    category=item.category,
                    priority=item.priority,
                )
            )
        for fid in item.supporting_finding_ids:
            if fid.startswith(_PRESENTATION_FINDING_PREFIX):
                out.append(
                    ClassifiedModernizationFact(
                        name=f"priority_action_authority:{label}",
                        rule_id="modernization.authority",
                        classification=FactClassification.FALSE_POSITIVE,
                        expectation="no presentation:finding: ids",
                        actual=f"finding_id={fid!r}",
                        diagnostic="presentation:finding: id in priority action chain",
                        category=item.category,
                        priority=item.priority,
                    )
                )
    return out


def _priority_action_legacy_recommendation_checks(
    priority_actions: tuple[ModernizationPriorityActionActual, ...],
    *,
    recommendations_by_id: dict[str, ModernizationRecommendationActual],
) -> list[ClassifiedModernizationFact]:
    out: list[ClassifiedModernizationFact] = []
    for item in priority_actions:
        for rid in item.supporting_recommendation_ids:
            rec = recommendations_by_id.get(rid)
            if rec is None:
                continue
            if _is_legacy_recommendation(rec) or not rec.supporting_finding_ids:
                out.append(
                    ClassifiedModernizationFact(
                        name=f"priority_action_authority:{item.action_id or item.title}",
                        rule_id="modernization.authority",
                        classification=FactClassification.FALSE_POSITIVE,
                        expectation="PA from finding-backed recommendation",
                        actual=f"recommendation_id={rid!r} type={rec.recommendation_type!r}",
                        diagnostic="PA from non-finding-backed recommendation",
                        category=item.category,
                        priority=item.priority,
                        assessment_head=rec.assessment_head,
                    )
                )
    return out


def _structural_roadmap_checks(
    initiatives: tuple[ModernizationRoadmapInitiativeActual, ...],
    *,
    priority_actions_by_id: dict[str, ModernizationPriorityActionActual],
    require_pa_backed: bool,
) -> list[ClassifiedModernizationFact]:
    out: list[ClassifiedModernizationFact] = []
    for item in initiatives:
        label = item.initiative_id or item.title
        initiative_type = (item.initiative_type or "").lower()
        if initiative_type == "legacy":
            # Legacy initiatives are structurally acceptable (not auto-FP).
            continue

        needs_pa = initiative_type in {"priority_action_backed", "merged"} or (
            require_pa_backed and initiative_type != "legacy"
        )
        if not needs_pa:
            continue

        if not item.supporting_priority_action_ids:
            out.append(
                ClassifiedModernizationFact(
                    name=f"roadmap_authority:{label}",
                    rule_id="modernization.authority",
                    classification=FactClassification.FALSE_POSITIVE,
                    expectation="supporting_priority_action_ids non-empty",
                    actual=(
                        f"initiative_type={item.initiative_type!r} "
                        "supporting_priority_action_ids=[]"
                    ),
                    diagnostic="roadmap bypasses priority actions",
                    category=item.phase,
                )
            )
            continue

        if item.primary_priority_action_id:
            primary = item.primary_priority_action_id
            if (
                primary not in item.supporting_priority_action_ids
                and primary not in priority_actions_by_id
            ):
                out.append(
                    ClassifiedModernizationFact(
                        name=f"roadmap_authority:{label}",
                        rule_id="modernization.authority",
                        classification=FactClassification.FALSE_POSITIVE,
                        expectation="primary_priority_action_id resolves",
                        actual=f"primary={primary!r}",
                        diagnostic="primary_priority_action_id does not resolve",
                        category=item.phase,
                    )
                )
    return out


def _recommendation_matches(
    expectation: ModernizationRecommendationExpectation,
    actual: ModernizationRecommendationActual,
) -> bool:
    has_criteria = bool(
        expectation.category
        or expectation.title_pattern
        or expectation.supporting_rule_ids
        or expectation.expected_priority
        or expectation.assessment_head
    )
    if not has_criteria:
        return False
    if expectation.category and _norm(actual.category or "") != _norm(expectation.category):
        return False
    if expectation.title_pattern:
        if not re.search(expectation.title_pattern, actual.title, flags=re.IGNORECASE):
            return False
    if expectation.expected_priority and _norm(actual.priority or "") != _norm(
        expectation.expected_priority
    ):
        return False
    if expectation.assessment_head:
        actual_head = actual.assessment_head or _normalize_assessment_head(actual.category)
        if _norm(actual_head or "") != _norm(
            _normalize_assessment_head(expectation.assessment_head)
            or expectation.assessment_head
        ):
            return False
    if expectation.supporting_rule_ids:
        actual_rules = set(actual.supporting_rule_ids)
        if not all(rule_id in actual_rules for rule_id in expectation.supporting_rule_ids):
            return False
    return True


def _priority_action_matches(
    expectation: ModernizationPriorityActionExpectation,
    actual: ModernizationPriorityActionActual,
    recommendations_by_id: dict[str, ModernizationRecommendationActual],
) -> bool:
    has_criteria = bool(
        expectation.title_pattern
        or expectation.supporting_recommendation_patterns
        or expectation.expected_priority
        or expectation.expected_horizon
        or expectation.category
    )
    if not has_criteria:
        return False
    if expectation.title_pattern:
        if not re.search(expectation.title_pattern, actual.title, flags=re.IGNORECASE):
            return False
    if expectation.expected_priority and _norm(actual.priority or "") != _norm(
        expectation.expected_priority
    ):
        return False
    if expectation.expected_horizon and _norm(actual.presentation_bucket or "") != _norm(
        expectation.expected_horizon
    ):
        return False
    if expectation.category and _norm(actual.category or "") != _norm(expectation.category):
        return False
    if expectation.supporting_recommendation_patterns:
        titles = [
            recommendations_by_id[rid].title
            for rid in actual.supporting_recommendation_ids
            if rid in recommendations_by_id
        ]
        # Fall back to ids/summary so patterns remain usable without rec lookup.
        haystacks = titles or list(actual.supporting_recommendation_ids)
        if actual.summary:
            haystacks.append(actual.summary)
        for pattern in expectation.supporting_recommendation_patterns:
            if not any(re.search(pattern, hay, flags=re.IGNORECASE) for hay in haystacks):
                return False
    return True


def _initiative_matches(
    expectation: ModernizationRoadmapInitiativeExpectation,
    actual: ModernizationRoadmapInitiativeActual,
    priority_actions_by_id: dict[str, ModernizationPriorityActionActual],
) -> bool:
    has_criteria = bool(
        expectation.title_pattern
        or expectation.phase
        or expectation.supporting_priority_action_patterns
        or expectation.initiative_type
    )
    if not has_criteria:
        return False
    if expectation.title_pattern:
        if not re.search(expectation.title_pattern, actual.title, flags=re.IGNORECASE):
            return False
    if expectation.phase and _norm_phase(actual.phase or "") != _norm_phase(expectation.phase):
        return False
    if expectation.initiative_type and _norm(actual.initiative_type or "") != _norm(
        expectation.initiative_type
    ):
        return False
    if expectation.supporting_priority_action_patterns:
        titles = [
            priority_actions_by_id[aid].title
            for aid in actual.supporting_priority_action_ids
            if aid in priority_actions_by_id
        ]
        haystacks = titles or list(actual.supporting_priority_action_ids)
        for pattern in expectation.supporting_priority_action_patterns:
            if not any(re.search(pattern, hay, flags=re.IGNORECASE) for hay in haystacks):
                return False
    return True


def _count_for_key(
    key: str,
    *,
    recommendations: tuple[ModernizationRecommendationActual, ...],
    priority_actions: tuple[ModernizationPriorityActionActual, ...],
    initiatives: tuple[ModernizationRoadmapInitiativeActual, ...],
) -> int:
    normalized = key.strip().lower()
    if normalized in {"finding_backed_recommendations", "finding_backed"}:
        return sum(1 for item in recommendations if _requires_finding_authority(item))
    if normalized in {"legacy_recommendations", "legacy"}:
        return sum(1 for item in recommendations if _is_legacy_recommendation(item))
    if normalized in {"recommendations", "deterministic_recommendations"}:
        return len(recommendations)
    if normalized in {"priority_actions", "priority_action"}:
        return len(priority_actions)
    if normalized in {"roadmap_initiatives", "initiatives"}:
        return len(initiatives)
    if normalized in _ROADMAP_PHASES or normalized.startswith("phase:"):
        phase = normalized.removeprefix("phase:")
        return sum(1 for item in initiatives if _norm_phase(item.phase or "") == phase)
    return sum(
        1
        for item in recommendations
        if (item.category and _norm(item.category) == normalized)
        or (item.assessment_head and _norm(item.assessment_head) == normalized)
        or key in item.supporting_rule_ids
        or any(_norm(rule_id) == normalized for rule_id in item.supporting_rule_ids)
    )


def _requires_finding_authority(item: ModernizationRecommendationActual) -> bool:
    rtype = (item.recommendation_type or "").lower()
    if rtype in _FINDING_BACKED_TYPES:
        return True
    rid = item.recommendation_id or ""
    return rid.startswith("recommendation:")


def _is_legacy_recommendation(item: ModernizationRecommendationActual) -> bool:
    rtype = (item.recommendation_type or "").lower()
    if rtype == "legacy":
        return True
    if rtype in _FINDING_BACKED_TYPES:
        return False
    if (item.recommendation_id or "").startswith("recommendation:"):
        return False
    return not item.supporting_finding_ids


def _recommendation_expect_text(item: ModernizationRecommendationExpectation) -> str:
    parts: list[str] = []
    if item.title_pattern:
        parts.append(f"title_pattern={item.title_pattern}")
    if item.category:
        parts.append(f"category={item.category}")
    if item.expected_priority:
        parts.append(f"priority={item.expected_priority}")
    if item.assessment_head:
        parts.append(f"assessment_head={item.assessment_head}")
    if item.supporting_rule_ids:
        parts.append(f"rules={','.join(item.supporting_rule_ids)}")
    if item.intent:
        parts.append(f"intent={item.intent}")
    return ",".join(parts) or "recommendation"


def _priority_action_expect_text(item: ModernizationPriorityActionExpectation) -> str:
    parts: list[str] = []
    if item.title_pattern:
        parts.append(f"title_pattern={item.title_pattern}")
    if item.category:
        parts.append(f"category={item.category}")
    if item.expected_priority:
        parts.append(f"priority={item.expected_priority}")
    if item.expected_horizon:
        parts.append(f"horizon={item.expected_horizon}")
    if item.supporting_recommendation_patterns:
        parts.append(
            "supporting_recommendation_patterns="
            + ",".join(item.supporting_recommendation_patterns)
        )
    return ",".join(parts) or "priority_action"


def _initiative_expect_text(item: ModernizationRoadmapInitiativeExpectation) -> str:
    parts: list[str] = []
    if item.title_pattern:
        parts.append(f"title_pattern={item.title_pattern}")
    if item.phase:
        parts.append(f"phase={item.phase}")
    if item.initiative_type:
        parts.append(f"initiative_type={item.initiative_type}")
    if item.supporting_priority_action_patterns:
        parts.append(
            "supporting_priority_action_patterns="
            + ",".join(item.supporting_priority_action_patterns)
        )
    return ",".join(parts) or "roadmap_initiative"


def _metrics_by_attr(
    classifications: list[ClassifiedModernizationFact],
    *,
    attr: str,
) -> tuple[ModernizationRuleMetrics, ...]:
    present = sorted(
        {(getattr(item, attr) or "unknown") for item in classifications}
    )
    metrics: list[ModernizationRuleMetrics] = []
    for key in present:
        scoped = [
            item for item in classifications if (getattr(item, attr) or "unknown") == key
        ]
        tp = sum(
            1 for item in scoped if item.classification is FactClassification.TRUE_POSITIVE
        )
        fp = sum(
            1 for item in scoped if item.classification is FactClassification.FALSE_POSITIVE
        )
        fn = sum(
            1 for item in scoped if item.classification is FactClassification.FALSE_NEGATIVE
        )
        amb = sum(
            1 for item in scoped if item.classification is FactClassification.AMBIGUOUS
        )
        precision, recall, reason = compute_precision_recall(
            true_positives=tp, false_positives=fp, false_negatives=fn
        )
        metrics.append(
            ModernizationRuleMetrics(
                rule_id=key,
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


def _derive_assessment_head(
    *,
    category: str | None,
    metadata: dict[str, Any],
    item: dict[str, Any],
) -> str | None:
    raw = (
        metadata.get("assessment_head")
        or metadata.get("head")
        or item.get("assessment_head")
        or category
    )
    return _normalize_assessment_head(raw)


def _normalize_assessment_head(value: Any) -> str | None:
    if value is None:
        return None
    raw = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    if not raw:
        return None
    if raw in _ASSESSMENT_HEAD_ALIASES:
        return _ASSESSMENT_HEAD_ALIASES[raw]
    # Strip common suffixes: security_intelligence → security
    for suffix in ("_intelligence", "_readiness", "_assessment"):
        if raw.endswith(suffix):
            stem = raw[: -len(suffix)]
            if stem in _ASSESSMENT_HEAD_ALIASES:
                return _ASSESSMENT_HEAD_ALIASES[stem]
            return stem
    return raw


def _string_id_tuple(values: Any) -> tuple[str, ...]:
    if not isinstance(values, list | tuple):
        return ()
    out: list[str] = []
    for item in values:
        if item is None:
            continue
        text = str(item).strip()
        if text:
            out.append(text)
    return tuple(sorted(set(out)))


def _claim_present(text: str, claim: str) -> bool:
    """True when ``claim`` appears as a phrase with word boundaries."""

    pattern = rf"(?<![a-z0-9_]){re.escape(claim)}(?![a-z0-9_])"
    return re.search(pattern, text) is not None


def _is_disclaimer_negation(text: str, claim: str) -> bool:
    patterns = (
        rf"do not certify {re.escape(claim)}",
        rf"does not certify {re.escape(claim)}",
        rf"does not establish {re.escape(claim)}",
        rf"does not establish",
        rf"do not establish",
        rf"were not assessed",
        rf"do not certify",
        rf"no engineering-hours",
        rf"staffing or schedule estimate is not",
        rf"absence of",
        rf"out of scope",
        rf"does not mean the repository is",
        rf"were not performed",
        rf"were not evaluated",
        rf"not performed",
    )
    return any(re.search(pattern, text) for pattern in patterns)


def _norm_phase(value: str) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def _norm(value: str) -> str:
    return value.strip().lower()
