"""Extract FalseNegativeRecord candidates from pack validation classifications."""

from __future__ import annotations

from codestrata.domain.quality_metrics.false_negatives import (
    FalseNegativeClassification,
    FalseNegativeEntityType,
    FalseNegativeRecord,
    FalseNegativeStatus,
    build_false_negative_record,
    merge_false_negative_records,
)
from validation.inventory import FactClassification
from validation.matrix import VALIDATION_MATRIX


_PACK_ENTITY_TYPES: dict[str, FalseNegativeEntityType] = {
    "technology_inventory": FalseNegativeEntityType.TECHNOLOGY_FACT,
    "security": FalseNegativeEntityType.FINDING,
    "architecture": FalseNegativeEntityType.FINDING,
    "technical_debt": FalseNegativeEntityType.FINDING,
    "dependency": FalseNegativeEntityType.FINDING,
    "cloud": FalseNegativeEntityType.FINDING,
    "ai_readiness": FalseNegativeEntityType.FINDING,
    "modernization": FalseNegativeEntityType.RECOMMENDATION,
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
    diagnostic: str,
) -> tuple[FalseNegativeClassification, FalseNegativeStatus, tuple[str, ...]]:
    text = (diagnostic or "").lower()
    if fact_classification is FactClassification.AMBIGUOUS:
        return (
            FalseNegativeClassification.AMBIGUOUS,
            FalseNegativeStatus.INVESTIGATING,
            ("ambiguous expected positive excluded from confirmed FN counts",),
        )
    if "unsupported" in text or "not claimed" in text or "not_claimed" in text:
        return (
            FalseNegativeClassification.UNSUPPORTED_CAPABILITY,
            FalseNegativeStatus.OPEN,
            ("unsupported or not-claimed capability; not a confirmed product FN",),
        )
    if "insufficient" in text or "unreadable" in text or "parse failed" in text:
        return (
            FalseNegativeClassification.INSUFFICIENT_EVIDENCE,
            FalseNegativeStatus.INVESTIGATING,
            ("insufficient evidence distinct from product detection failure",),
        )
    if fact_classification is FactClassification.FALSE_NEGATIVE:
        if _is_controlled_fixture(repository_id):
            return (
                FalseNegativeClassification.CONFIRMED,
                FalseNegativeStatus.OPEN,
                (
                    "auto-confirmed: controlled fixture with explicit required "
                    "expected positive",
                ),
            )
        return (
            FalseNegativeClassification.SUSPECTED,
            FalseNegativeStatus.OPEN,
            (
                "real-world or non-fixture repository; remains suspected until "
                "adjudicated",
            ),
        )
    raise ValueError(f"unsupported fact classification for FN tracking: {fact_classification}")


def candidates_from_pack_result(
    pack: str,
    result: object,
    *,
    run_id: str,
) -> tuple[FalseNegativeRecord, ...]:
    """Build FN candidates from pack ``classifications`` (structured only)."""

    repository_id = str(getattr(result, "repository_id", "") or "unknown")
    default_entity_type = _PACK_ENTITY_TYPES.get(pack, FalseNegativeEntityType.OTHER)
    records: list[FalseNegativeRecord] = []
    classifications = getattr(result, "classifications", ()) or ()
    for item in classifications:
        classification = getattr(item, "classification", None)
        if classification is FactClassification.AMBIGUOUS:
            fact_class = FactClassification.AMBIGUOUS
        elif classification is FactClassification.FALSE_NEGATIVE:
            fact_class = FactClassification.FALSE_NEGATIVE
        else:
            continue
        diagnostic = str(getattr(item, "diagnostic", "") or "")
        fn_class, status, limitations = _initial_classification(
            fact_classification=fact_class,
            repository_id=repository_id,
            diagnostic=diagnostic,
        )
        rule_id = getattr(item, "rule_id", None)
        category = getattr(item, "category", None)
        name = getattr(item, "name", None)
        path = getattr(item, "path", None)
        entity_type = default_entity_type
        notes = list(limitations)

        if pack == "technology_inventory":
            assessment_area = f"technology_inventory:{category or 'unknown'}"
            expected_entity_id = str(name) if name else None
            expected_rule_id = None
            expected_category = str(category) if category else None
            if not expected_entity_id and not expected_category:
                notes.append("false_negative_identity_unavailable")
                continue
        elif pack == "modernization":
            assessment_area = f"modernization:{rule_id or name or 'unknown'}"
            expected_entity_id = str(name) if name else None
            expected_rule_id = str(rule_id) if rule_id else None
            expected_category = str(getattr(item, "category", None) or "") or None
            if getattr(item, "priority", None):
                entity_type = FalseNegativeEntityType.PRIORITY_ACTION
            if not expected_rule_id and not expected_entity_id:
                notes.append("false_negative_identity_unavailable")
                continue
        else:
            assessment_area = f"{pack}:{rule_id or name or 'unknown'}"
            expected_entity_id = str(name) if name else None
            expected_rule_id = str(rule_id) if rule_id else None
            expected_category = str(category) if category else None
            if not expected_rule_id and not expected_entity_id:
                notes.append("false_negative_identity_unavailable")
                continue

        if path is None and pack != "technology_inventory":
            notes.append(
                "expected_path unavailable on classification; identity uses rule/entity"
            )

        records.append(
            build_false_negative_record(
                repository_id=repository_id,
                assessment_area=assessment_area,
                entity_type=entity_type,
                expected=getattr(item, "expectation", ""),
                actual=getattr(item, "actual", "absent"),
                diagnostic=diagnostic or "false negative",
                run_id=run_id,
                expected_rule_id=expected_rule_id,
                expected_entity_id=expected_entity_id,
                expected_category=expected_category,
                expected_path=path,
                expected_subject=str(name) if name else None,
                classification=fn_class,
                status=status,
                limitations=notes,
            )
        )
    return merge_false_negative_records(records)
