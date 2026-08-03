"""Deterministic pattern subject identities (no titles / AI / fuzzy matching)."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.intelligence_reporting.domain.enums import PatternType

# Configuration-condition rule markers (rule_id substrings, not values).
_CONFIGURATION_MARKERS = (
    "credential",
    "debug",
    "tls",
    "authentication",
    "auth-disabled",
    "placeholder",
    "insecure",
)


@dataclass(frozen=True, slots=True)
class RecurringPatternSubject:
    subject_type: str
    normalized_identity: str
    rule_ids: tuple[str, ...] = ()
    assessment_head_ids: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    @property
    def normalized_subject(self) -> str:
        return f"{self.subject_type}:{self.normalized_identity}"


def classify_rule_pattern_type(rule_id: str) -> PatternType:
    rid = rule_id.strip().lower()
    if rid.startswith("dependency.") or ".dependency." in rid:
        return PatternType.RECURRING_DEPENDENCY_CONDITION
    if rid.startswith("architecture.") or ".architecture." in rid:
        return PatternType.RECURRING_ARCHITECTURE_CONDITION
    if (
        rid.startswith("technical_debt.")
        or rid.startswith("complexity.")
        or ".technical_debt." in rid
    ):
        return PatternType.RECURRING_COMPLEXITY_CONDITION
    if any(marker in rid for marker in _CONFIGURATION_MARKERS):
        return PatternType.RECURRING_CONFIGURATION_CONDITION
    return PatternType.RECURRING_RULE


def rule_subject(*, rule_id: str, assessment_head_id: str) -> RecurringPatternSubject:
    return RecurringPatternSubject(
        subject_type="rule",
        normalized_identity=f"{assessment_head_id}|{rule_id.strip()}",
        rule_ids=(rule_id.strip(),),
        assessment_head_ids=(assessment_head_id,),
    )


def recommendation_subject(
    *,
    provider_id: str | None,
    category: str,
    assessment_head_id: str,
) -> RecurringPatternSubject | None:
    provider = (provider_id or "").strip()
    cat = category.strip().lower().replace(" ", "_").replace("-", "_")
    if not provider and not cat:
        return None
    identity = f"{assessment_head_id}|provider:{provider or 'none'}|category:{cat or 'none'}"
    limitations: tuple[str, ...] = ()
    if not provider:
        limitations = ("recommendation_identity_uses_category_without_provider",)
    return RecurringPatternSubject(
        subject_type="recommendation",
        normalized_identity=identity,
        assessment_head_ids=(assessment_head_id,),
        limitations=limitations,
    )


def technology_conflict_subject(
    *,
    category: str,
    normalized_name: str,
) -> RecurringPatternSubject:
    cat = category.strip().lower().replace(" ", "_")
    name = normalized_name.strip().lower()
    return RecurringPatternSubject(
        subject_type="technology_conflict",
        normalized_identity=f"{cat}|{name}",
        assessment_head_ids=("technology_inventory",),
        limitations=("technology_prevalence_belongs_in_technology_distribution",),
    )
