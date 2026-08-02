"""Historical false-positive tracking across Slice 4.11 runs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from codestrata.domain.quality_metrics.false_positives import (
    FalsePositiveClassification,
    FalsePositiveRecord,
    FalsePositiveStatus,
    merge_false_positive_records,
    summarize_false_positives,
)
from validation.false_positives.adjudication import (
    ADJUDICATIONS_DIR,
    apply_adjudication,
    load_adjudications,
)
from validation.false_positives.candidates import (
    candidates_from_comparison_outcome,
    candidates_from_pack_result,
)
from validation.models import ComparisonOutcome, ValidationVerdict
from validation.paths import RESULTS_DIR
from validation.recording import (
    RepositoryValidationRecord,
    list_run_ids,
    load_repository_validation_record,
    repository_records_root,
)


def _records_from_payload(items: list[Any] | tuple[Any, ...]) -> tuple[FalsePositiveRecord, ...]:
    out: list[FalsePositiveRecord] = []
    for item in items:
        if isinstance(item, FalsePositiveRecord):
            out.append(item)
        elif isinstance(item, dict):
            out.append(FalsePositiveRecord.model_validate(item))
    return tuple(out)


def load_historical_false_positives(
    repository_id: str,
    *,
    records_root: Path = RESULTS_DIR,
    exclude_run_id: str | None = None,
) -> tuple[FalsePositiveRecord, ...]:
    """Load FP rows from prior successful comparable runs for one repository."""

    collected: list[FalsePositiveRecord] = []
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
        except Exception:  # noqa: BLE001 — skip unreadable historical records
            continue
        if record.verdict in {ValidationVerdict.SKIPPED, ValidationVerdict.ERROR}:
            continue
        collected.extend(_records_from_payload(record.false_positives))
    return merge_false_positive_records(collected)


def apply_run_history(
    current: tuple[FalsePositiveRecord, ...],
    historical: tuple[FalsePositiveRecord, ...],
    *,
    current_run_id: str,
    verdict: ValidationVerdict,
) -> tuple[FalsePositiveRecord, ...]:
    """Update first/last seen and optionally resolve absent adjudicated FPs.

    Skip/error verdicts never resolve open FPs.
    """

    if verdict in {ValidationVerdict.SKIPPED, ValidationVerdict.ERROR}:
        # Preserve history but do not treat absence as resolution.
        return merge_false_positive_records((*historical, *current))

    current_ids = {item.false_positive_id for item in current}
    merged = merge_false_positive_records((*historical, *current))
    updated: list[FalsePositiveRecord] = []
    for item in merged:
        if item.false_positive_id in current_ids:
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
        # Absent from current successful run.
        if (
            item.status is FalsePositiveStatus.FIXED
            or item.classification
            in {
                FalsePositiveClassification.REJECTED,
                FalsePositiveClassification.EXPECTATION_ERROR,
            }
        ):
            updated.append(item)
            continue
        # Only mark fixed when adjudication already declared fixed and resolution exists.
        if item.status is FalsePositiveStatus.FIXED and item.resolution is not None:
            updated.append(
                item.model_copy(
                    update={
                        "resolved_run_id": item.resolved_run_id or current_run_id,
                        "limitations": tuple(
                            sorted(
                                set(item.limitations)
                                | {
                                    "absent from successful comparable run after adjudicated fix"
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
                                    "absent from later successful run but not auto-resolved "
                                    "(requires adjudication)"
                                }
                            )
                        ),
                    }
                )
            )
    return merge_false_positive_records(updated)


def collect_false_positives_for_record(
    *,
    repository_id: str,
    run_id: str,
    verdict: ValidationVerdict,
    outcome: ComparisonOutcome | None,
    pack_results: dict[str, Any] | None = None,
    records_root: Path = RESULTS_DIR,
    adjudications_dir: Path = ADJUDICATIONS_DIR,
) -> tuple[tuple[FalsePositiveRecord, ...], dict[str, int]]:
    """Build adjudicated + historically merged FP list for one repository run."""

    current: tuple[FalsePositiveRecord, ...] = ()
    if outcome is not None:
        current = candidates_from_comparison_outcome(
            outcome,
            run_id=run_id,
            pack_results=pack_results,
        )
    elif pack_results:
        collected: list[FalsePositiveRecord] = []
        for pack, result in sorted(pack_results.items()):
            collected.extend(candidates_from_pack_result(pack, result, run_id=run_id))
        current = merge_false_positive_records(collected)

    adjudications = load_adjudications(adjudications_dir=adjudications_dir)
    adjudicated = tuple(
        apply_adjudication(
            item,
            adjudications.get(item.false_positive_id),
            resolved_run_id=run_id if verdict == ValidationVerdict.PASS else None,
        )
        for item in current
    )
    historical = load_historical_false_positives(
        repository_id,
        records_root=records_root,
        exclude_run_id=run_id,
    )
    # Re-apply adjudications to historical rows as well (committed source of truth).
    historical = tuple(
        apply_adjudication(item, adjudications.get(item.false_positive_id))
        for item in historical
    )
    merged = apply_run_history(
        adjudicated,
        historical,
        current_run_id=run_id,
        verdict=verdict,
    )
    summary = summarize_false_positives(merged).model_dump(mode="json")
    return merged, summary
