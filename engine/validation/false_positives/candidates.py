"""Extract FalsePositiveRecord candidates from pack validation classifications."""

from __future__ import annotations

from typing import Any

from codestrata.domain.quality_metrics.false_positives import (
    FalsePositiveClassification,
    FalsePositiveEntityType,
    FalsePositiveRecord,
    FalsePositiveStatus,
    build_false_positive_record,
    merge_false_positive_records,
)
from validation.inventory import FactClassification
from validation.matrix import VALIDATION_MATRIX
from validation.models import ComparisonMismatch, ComparisonOutcome


_PACK_ENTITY_TYPES: dict[str, FalsePositiveEntityType] = {
    "technology_inventory": FalsePositiveEntityType.TECHNOLOGY_FACT,
    "security": FalsePositiveEntityType.FINDING,
    "architecture": FalsePositiveEntityType.FINDING,
    "technical_debt": FalsePositiveEntityType.FINDING,
    "dependency": FalsePositiveEntityType.FINDING,
    "cloud": FalsePositiveEntityType.FINDING,
    "ai_readiness": FalsePositiveEntityType.FINDING,
    "modernization": FalsePositiveEntityType.RECOMMENDATION,
}


def _is_controlled_fixture(repository_id: str) -> bool:
    row = VALIDATION_MATRIX.get(repository_id) or {}
    return str(row.get("controlled_vs_real_world", "")).lower() in {
        "controlled",
        "controlled-fixture",
        "fixture",
    }


def _initial_classification(
    *,
    fact_classification: FactClassification,
    repository_id: str,
) -> tuple[FalsePositiveClassification, FalsePositiveStatus, tuple[str, ...]]:
    if fact_classification is FactClassification.AMBIGUOUS:
        return (
            FalsePositiveClassification.AMBIGUOUS,
            FalsePositiveStatus.INVESTIGATING,
            ("ambiguous observation excluded from confirmed FP counts",),
        )
    if fact_classification is FactClassification.FALSE_POSITIVE:
        if _is_controlled_fixture(repository_id):
            return (
                FalsePositiveClassification.CONFIRMED,
                FalsePositiveStatus.OPEN,
                (
                    "auto-confirmed: controlled fixture with explicit forbidden expectation",
                ),
            )
        return (
            FalsePositiveClassification.SUSPECTED,
            FalsePositiveStatus.OPEN,
            ("real-world or non-fixture repository; remains suspected until adjudicated",),
        )
    # Non-FP classifications are not tracked here.
    raise ValueError(f"unsupported fact classification for FP tracking: {fact_classification}")


def candidates_from_pack_result(
    pack: str,
    result: object,
    *,
    run_id: str,
) -> tuple[FalsePositiveRecord, ...]:
    """Build FP candidates from pack ``classifications`` (structured only)."""

    repository_id = str(getattr(result, "repository_id", "") or "unknown")
    default_entity_type = _PACK_ENTITY_TYPES.get(pack, FalsePositiveEntityType.OTHER)
    records: list[FalsePositiveRecord] = []
    classifications = getattr(result, "classifications", ()) or ()
    for item in classifications:
        classification = getattr(item, "classification", None)
        if classification is FactClassification.AMBIGUOUS:
            fact_class = FactClassification.AMBIGUOUS
        elif classification is FactClassification.FALSE_POSITIVE:
            fact_class = FactClassification.FALSE_POSITIVE
        else:
            continue
        fp_class, status, limitations = _initial_classification(
            fact_classification=fact_class,
            repository_id=repository_id,
        )
        rule_id = getattr(item, "rule_id", None)
        category = getattr(item, "category", None)
        name = getattr(item, "name", None)
        path = getattr(item, "path", None)
        entity_type = default_entity_type
        if pack == "technology_inventory":
            assessment_area = f"technology_inventory:{category or 'unknown'}"
            entity_id = str(name) if name else None
            rule = None
        elif pack == "modernization":
            assessment_area = f"modernization:{rule_id or name or 'unknown'}"
            entity_id = str(name) if name else None
            rule = str(rule_id) if rule_id else None
            if getattr(item, "priority", None):
                entity_type = FalsePositiveEntityType.PRIORITY_ACTION
        else:
            assessment_area = f"{pack}:{rule_id or name or 'unknown'}"
            entity_id = str(name) if name else None
            rule = str(rule_id) if rule_id else None
        notes = list(limitations)
        if path is None and pack != "technology_inventory":
            notes.append("path unavailable on classification; identity uses rule/entity only")
        records.append(
            build_false_positive_record(
                repository_id=repository_id,
                assessment_area=assessment_area,
                entity_type=entity_type,
                expected=getattr(item, "expectation", ""),
                actual=getattr(item, "actual", ""),
                diagnostic=getattr(item, "diagnostic", ""),
                run_id=run_id,
                rule_id=rule,
                entity_id=entity_id,
                path=path,
                classification=fp_class,
                status=status,
                limitations=notes,
            )
        )
    return merge_false_positive_records(records)


def candidates_from_mismatches(
    mismatches: tuple[ComparisonMismatch, ...] | list[ComparisonMismatch],
    *,
    run_id: str,
    already_tracked_ids: set[str] | None = None,
) -> tuple[FalsePositiveRecord, ...]:
    """Project residual mismatches that look like FPs but lack pack classification rows.

    Only used when structured classification identity is absent. Adds an explicit
    limitation and never fabricates confirmed product FPs from prose alone.
    """

    tracked = already_tracked_ids or set()
    records: list[FalsePositiveRecord] = []
    for mismatch in mismatches:
        area = mismatch.assessment_area
        # FN-oriented diagnostics are excluded (Slice 5.10).
        diagnostic_l = mismatch.diagnostic.lower()
        if "false_negative" in diagnostic_l or "missing required" in diagnostic_l:
            continue
        if "false_positive" not in diagnostic_l and "forbidden" not in diagnostic_l:
            # Generic mismatches without FP signal remain untracked.
            continue
        record = build_false_positive_record(
            repository_id=mismatch.repository_id,
            assessment_area=area,
            entity_type=FalsePositiveEntityType.OTHER,
            expected=mismatch.expectation,
            actual=mismatch.actual,
            diagnostic=mismatch.diagnostic,
            run_id=run_id,
            classification=FalsePositiveClassification.SUSPECTED,
            status=FalsePositiveStatus.OPEN,
            limitations=(
                "projected from ComparisonMismatch without structured pack classification",
            ),
        )
        if record.false_positive_id in tracked:
            continue
        records.append(record)
    return merge_false_positive_records(records)


def candidates_from_comparison_outcome(
    outcome: ComparisonOutcome,
    *,
    run_id: str,
    pack_results: dict[str, Any] | None = None,
) -> tuple[FalsePositiveRecord, ...]:
    """Collect FP candidates from pack results attached during comparison."""

    collected: list[FalsePositiveRecord] = []
    pack_results = pack_results or {}
    for pack, result in sorted(pack_results.items()):
        collected.extend(candidates_from_pack_result(pack, result, run_id=run_id))
    tracked = {item.false_positive_id for item in collected}
    # Residual mismatch projection is intentionally conservative.
    collected.extend(
        candidates_from_mismatches(
            outcome.mismatches,
            run_id=run_id,
            already_tracked_ids=tracked,
        )
    )
    return merge_false_positive_records(collected)
