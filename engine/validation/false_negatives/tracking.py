"""Historical false-negative tracking across Slice 4.11 runs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from codestrata.domain.quality_metrics.false_negatives import (
    FalseNegativeClassification,
    FalseNegativeRecord,
    FalseNegativeStatus,
    merge_false_negative_records,
    summarize_false_negatives,
)
from validation.false_negatives.adjudication import (
    ADJUDICATIONS_DIR,
    apply_adjudication,
    load_adjudications,
)
from validation.false_negatives.candidates import candidates_from_pack_result
from validation.models import ComparisonOutcome, ValidationVerdict
from validation.paths import RESULTS_DIR
from validation.recording import (
    list_run_ids,
    load_repository_validation_record,
    repository_records_root,
)


def _records_from_payload(items: list[Any] | tuple[Any, ...]) -> tuple[FalseNegativeRecord, ...]:
    out: list[FalseNegativeRecord] = []
    for item in items:
        if isinstance(item, FalseNegativeRecord):
            out.append(item)
        elif isinstance(item, dict):
            out.append(FalseNegativeRecord.model_validate(item))
    return tuple(out)


def load_historical_false_negatives(
    repository_id: str,
    *,
    records_root: Path = RESULTS_DIR,
    exclude_run_id: str | None = None,
) -> tuple[FalseNegativeRecord, ...]:
    """Load FN rows from prior successful comparable runs for one repository."""

    collected: list[FalseNegativeRecord] = []
    for run_id in list_run_ids(repository_id, records_root=records_root):
        if exclude_run_id and run_id == exclude_run_id:
            continue
        record_dir = (
            repository_records_root(repository_id, records_root=records_root)
            / "runs"
            / run_id
        )
        try:
            record = load_repository_validation_record(record_dir)
        except Exception:  # noqa: BLE001
            continue
        if record.verdict in {ValidationVerdict.SKIPPED, ValidationVerdict.ERROR}:
            continue
        collected.extend(_records_from_payload(getattr(record, "false_negatives", ()) or ()))
    return merge_false_negative_records(collected)


def apply_run_history(
    current: tuple[FalseNegativeRecord, ...],
    historical: tuple[FalseNegativeRecord, ...],
    *,
    current_run_id: str,
    verdict: ValidationVerdict,
) -> tuple[FalseNegativeRecord, ...]:
    """Update first/last seen; never auto-resolve from skip/error/disabled runs."""

    if verdict in {ValidationVerdict.SKIPPED, ValidationVerdict.ERROR}:
        return merge_false_negative_records((*historical, *current))

    current_ids = {item.false_negative_id for item in current}
    merged = merge_false_negative_records((*historical, *current))
    updated: list[FalseNegativeRecord] = []
    for item in merged:
        if item.false_negative_id in current_ids:
            updated.append(
                item.model_copy(
                    update={
                        "last_seen_run_id": max(item.last_seen_run_id, current_run_id),
                        "observation_run_ids": tuple(
                            sorted(set(item.observation_run_ids) | {current_run_id})
                        ),
                    }
                )
            )
            continue
        if item.status is FalseNegativeStatus.FIXED or item.classification in {
            FalseNegativeClassification.REJECTED,
            FalseNegativeClassification.EXPECTATION_ERROR,
            FalseNegativeClassification.UNSUPPORTED_CAPABILITY,
        }:
            updated.append(item)
            continue
        if item.status is FalseNegativeStatus.FIXED and item.resolution is not None:
            updated.append(
                item.model_copy(
                    update={
                        "resolved_run_id": item.resolved_run_id or current_run_id,
                        "limitations": tuple(
                            sorted(
                                set(item.limitations)
                                | {
                                    "absent from successful comparable run after "
                                    "adjudicated fix (expected positive now detected)"
                                }
                            )
                        ),
                    }
                )
            )
        else:
            updated.append(
                item.model_copy(
                    update={
                        "limitations": tuple(
                            sorted(
                                set(item.limitations)
                                | {
                                    "absent from later successful run but not "
                                    "auto-resolved (requires adjudication / TP "
                                    "confirmation)"
                                }
                            )
                        ),
                    }
                )
            )
    return merge_false_negative_records(updated)


def collect_false_negatives_for_record(
    *,
    repository_id: str,
    run_id: str,
    verdict: ValidationVerdict,
    outcome: ComparisonOutcome | None,
    pack_results: dict[str, Any] | None = None,
    records_root: Path = RESULTS_DIR,
    adjudications_dir: Path = ADJUDICATIONS_DIR,
) -> tuple[tuple[FalseNegativeRecord, ...], dict[str, int]]:
    """Build adjudicated + historically merged FN list for one repository run."""

    current: tuple[FalseNegativeRecord, ...] = ()
    if outcome is not None and getattr(outcome, "false_negatives", None):
        current = _records_from_payload(outcome.false_negatives)
    elif pack_results:
        collected: list[FalseNegativeRecord] = []
        for pack, result in sorted(pack_results.items()):
            collected.extend(candidates_from_pack_result(pack, result, run_id=run_id))
        current = merge_false_negative_records(collected)

    adjudications = load_adjudications(adjudications_dir=adjudications_dir)
    adjudicated = tuple(
        apply_adjudication(
            item,
            adjudications.get(item.false_negative_id),
            resolved_run_id=run_id if verdict == ValidationVerdict.PASS else None,
        )
        for item in current
    )
    historical = load_historical_false_negatives(
        repository_id,
        records_root=records_root,
        exclude_run_id=run_id,
    )
    historical = tuple(
        apply_adjudication(item, adjudications.get(item.false_negative_id))
        for item in historical
    )
    merged = apply_run_history(
        adjudicated,
        historical,
        current_run_id=run_id,
        verdict=verdict,
    )
    summary = summarize_false_negatives(merged).model_dump(mode="json")
    return merged, summary
