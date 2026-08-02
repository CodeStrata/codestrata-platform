"""Build ValidationSummaryArtifact from Slice 4.11 records (Epic 4 Slice 4.12).

Record-only, offline. Does not rerun assessments or mutate repository records.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from validation.coverage_gaps import derive_coverage_gaps
from validation.inventory import compute_precision_recall
from validation.matrix import VALIDATION_MATRIX
from validation.models import ValidationVerdict
from validation.paths import RESULTS_DIR
from validation.recording import (
    RECORD_SCHEMA_VERSION,
    RepositoryValidationRecord,
    list_run_ids,
    load_repository_validation_record,
    repository_records_root,
)
from validation.summary_artifact import (
    CANONICAL_PACKS,
    DISCLAIMER,
    SUMMARY_SCHEMA_VERSION,
    SUPPORTED_RECORD_SCHEMA_VERSION,
    ExpectationTotals,
    FalseNegativeSummaryAggregate,
    FalsePositiveSummaryAggregate,
    MismatchSummaryEntry,
    OverallVerdict,
    PackAggregateSummary,
    RepositorySummaryRow,
    SourceRecordRef,
    SummaryScope,
    ValidationSummaryArtifact,
    VerdictTotals,
)

_ABS_PATH_RE = re.compile(r"(^/)|(^[A-Za-z]:[\\/])|(/Users/)|(/home/)|(\\Users\\)")


class RecordValidationError(ValueError):
    """Malformed or unsupported Slice 4.11 validation record."""


def validate_repository_record(record: RepositoryValidationRecord) -> None:
    """Fail-closed validation of a loaded record before summarization."""

    if record.record_schema_version != SUPPORTED_RECORD_SCHEMA_VERSION:
        raise RecordValidationError(
            f"unsupported record_schema_version={record.record_schema_version!r}; "
            f"expected {SUPPORTED_RECORD_SCHEMA_VERSION!r}"
        )
    if not record.repository_id or not str(record.repository_id).strip():
        raise RecordValidationError("repository_id is required")
    if not record.run_id or not str(record.run_id).strip():
        raise RecordValidationError("run_id is required")
    try:
        ValidationVerdict(record.verdict.value if hasattr(record.verdict, "value") else record.verdict)
    except Exception as exc:  # noqa: BLE001
        raise RecordValidationError(f"invalid verdict: {record.verdict!r}") from exc

    if record.expectations_evaluated < 0 or record.expectations_matched < 0:
        raise RecordValidationError("expectation counts must be non-negative")
    if record.expectations_matched > record.expectations_evaluated:
        raise RecordValidationError(
            f"{record.repository_id}: expectations_matched "
            f"({record.expectations_matched}) > expectations_evaluated "
            f"({record.expectations_evaluated})"
        )

    mismatched = record.expectations_evaluated - record.expectations_matched
    if record.verdict == ValidationVerdict.PASS and record.mismatches:
        raise RecordValidationError(
            f"{record.repository_id}: PASS verdict with non-empty mismatches"
        )
    if record.verdict == ValidationVerdict.PASS and mismatched != 0:
        raise RecordValidationError(
            f"{record.repository_id}: PASS with unmatched expectations "
            f"({record.expectations_matched}/{record.expectations_evaluated})"
        )

    for pack in record.pack_precision:
        for field in (
            "true_positives",
            "false_positives",
            "false_negatives",
            "ambiguous",
        ):
            value = int(getattr(pack, field))
            if value < 0:
                raise RecordValidationError(
                    f"{record.repository_id}: pack {pack.pack} has negative {field}"
                )
        expected_p, expected_r, _ = compute_precision_recall(
            true_positives=pack.true_positives,
            false_positives=pack.false_positives,
            false_negatives=pack.false_negatives,
        )
        if pack.precision is None and expected_p is not None:
            raise RecordValidationError(
                f"{record.repository_id}: pack {pack.pack} missing precision"
            )
        if pack.precision is not None and expected_p is None:
            raise RecordValidationError(
                f"{record.repository_id}: pack {pack.pack} precision present but TP+FP=0"
            )
        if pack.precision is not None and expected_p is not None:
            if abs(float(pack.precision) - expected_p) > 1e-9:
                raise RecordValidationError(
                    f"{record.repository_id}: pack {pack.pack} precision inconsistent"
                )
        if pack.recall is None and expected_r is not None:
            raise RecordValidationError(
                f"{record.repository_id}: pack {pack.pack} missing recall"
            )
        if pack.recall is not None and expected_r is None:
            raise RecordValidationError(
                f"{record.repository_id}: pack {pack.pack} recall present but TP+FN=0"
            )
        if pack.recall is not None and expected_r is not None:
            if abs(float(pack.recall) - expected_r) > 1e-9:
                raise RecordValidationError(
                    f"{record.repository_id}: pack {pack.pack} recall inconsistent"
                )
        if pack.precision_metric is not None:
            from codestrata.domain.quality_metrics.precision import PrecisionMetric

            try:
                metric = PrecisionMetric.model_validate(pack.precision_metric)
            except Exception as exc:  # noqa: BLE001
                raise RecordValidationError(
                    f"{record.repository_id}: pack {pack.pack} invalid precision_metric"
                ) from exc
            if metric.true_positive_count != pack.true_positives:
                raise RecordValidationError(
                    f"{record.repository_id}: pack {pack.pack} "
                    "precision_metric TP mismatch"
                )
            if metric.false_positive_count != pack.false_positives:
                raise RecordValidationError(
                    f"{record.repository_id}: pack {pack.pack} "
                    "precision_metric FP mismatch"
                )
            if pack.precision_metric_id and pack.precision_metric_id != metric.metric_id:
                raise RecordValidationError(
                    f"{record.repository_id}: pack {pack.pack} "
                    "precision_metric_id mismatch"
                )
        if pack.recall_metric is not None:
            from codestrata.domain.quality_metrics.recall import RecallMetric

            try:
                recall_metric = RecallMetric.model_validate(pack.recall_metric)
            except Exception as exc:  # noqa: BLE001
                raise RecordValidationError(
                    f"{record.repository_id}: pack {pack.pack} invalid recall_metric"
                ) from exc
            if recall_metric.true_positive_count != pack.true_positives:
                raise RecordValidationError(
                    f"{record.repository_id}: pack {pack.pack} "
                    "recall_metric TP mismatch"
                )
            if recall_metric.false_negative_count != pack.false_negatives:
                raise RecordValidationError(
                    f"{record.repository_id}: pack {pack.pack} "
                    "recall_metric FN mismatch"
                )
            if pack.recall_metric_id and pack.recall_metric_id != recall_metric.metric_id:
                raise RecordValidationError(
                    f"{record.repository_id}: pack {pack.pack} "
                    "recall_metric_id mismatch"
                )

    if record.record_dir:
        _assert_safe_ref(record.record_dir, field="record_dir")
    for mismatch in record.mismatches:
        if mismatch.artifact_path:
            _assert_safe_ref(mismatch.artifact_path, field="mismatch.artifact_path")


def _assert_safe_ref(value: str, *, field: str) -> None:
    if _ABS_PATH_RE.search(value.replace("\\", "/")):
        raise RecordValidationError(f"{field} contains absolute/unsafe path: {value!r}")


def list_repository_ids_with_records(*, records_root: Path = RESULTS_DIR) -> tuple[str, ...]:
    if not records_root.is_dir():
        return ()
    ids: list[str] = []
    for path in sorted(records_root.iterdir()):
        if not path.is_dir():
            continue
        if path.name in {"summaries", "_records"}:
            continue
        if (path / "latest" / "record.json").is_file():
            ids.append(path.name)
            continue
        if list_run_ids(path.name, records_root=records_root):
            ids.append(path.name)
    return tuple(ids)


def load_records_for_summary(
    *,
    records_root: Path = RESULTS_DIR,
    repository_ids: set[str] | None = None,
    run_ids: Mapping[str, str] | None = None,
    prefer_latest: bool = True,
    require_all_requested: bool = False,
) -> tuple[tuple[RepositoryValidationRecord, SourceRecordRef], ...]:
    """Load and validate selected records. Fail-closed on malformed records.

    When ``repository_ids`` is provided and ``require_all_requested`` is false
    (default for tag/local filters), missing records are skipped. Explicit
    ``--repository`` selections should set ``require_all_requested=True``.
    """

    available = list_repository_ids_with_records(records_root=records_root)
    if repository_ids is not None:
        missing = sorted(set(repository_ids) - set(available))
        if require_all_requested and missing:
            raise RecordValidationError(
                f"no validation records found for: {', '.join(missing)}"
            )
        selected = sorted(set(repository_ids) & set(available))
    else:
        selected = list(available)

    if not selected:
        raise RecordValidationError("no validation records available to summarize")

    loaded: list[tuple[RepositoryValidationRecord, SourceRecordRef]] = []
    for repository_id in selected:
        if run_ids and repository_id in run_ids:
            run_id = run_ids[repository_id]
            record_dir = (
                repository_records_root(repository_id, records_root=records_root)
                / "runs"
                / run_id
            )
            relative = f"{repository_id}/runs/{run_id}/record.json"
        elif prefer_latest:
            record_dir = (
                repository_records_root(repository_id, records_root=records_root) / "latest"
            )
            relative = f"{repository_id}/latest/record.json"
        else:
            ids = list_run_ids(repository_id, records_root=records_root)
            if not ids:
                raise RecordValidationError(f"no runs for {repository_id}")
            run_id = ids[-1]
            record_dir = (
                repository_records_root(repository_id, records_root=records_root)
                / "runs"
                / run_id
            )
            relative = f"{repository_id}/runs/{run_id}/record.json"

        try:
            record = load_repository_validation_record(record_dir)
        except FileNotFoundError as exc:
            raise RecordValidationError(str(exc)) from exc
        except Exception as exc:  # noqa: BLE001 - treat parse failures as record errors
            raise RecordValidationError(
                f"malformed record at {relative}: {exc}"
            ) from exc

        if record.repository_id != repository_id:
            raise RecordValidationError(
                f"record repository_id mismatch: path={repository_id} "
                f"payload={record.repository_id}"
            )
        validate_repository_record(record)
        ref = SourceRecordRef(
            repository_id=repository_id,
            run_id=record.run_id,
            relative_path=relative,
        )
        loaded.append((record, ref))
    return tuple(loaded)


def derive_overall_verdict(verdicts: tuple[ValidationVerdict, ...]) -> OverallVerdict:
    """ERROR > FAIL > PASS > SKIPPED.

    Policy:
    - Any ERROR → ERROR
    - Else any FAIL → FAIL
    - Else any PASS → PASS (remote/network SKIPPED does not fail accuracy)
    - Else all SKIPPED / empty → SKIPPED
    Unavailable pack precision is never a failure by itself.
    """

    if any(item == ValidationVerdict.ERROR for item in verdicts):
        return OverallVerdict.ERROR
    if any(item == ValidationVerdict.FAIL for item in verdicts):
        return OverallVerdict.FAIL
    if any(item == ValidationVerdict.PASS for item in verdicts):
        return OverallVerdict.PASS
    return OverallVerdict.SKIPPED


def _source_identity(repository_id: str) -> str | None:
    row = VALIDATION_MATRIX.get(repository_id)
    if not row:
        return None
    return row.get("pinned_source_identity")


def _limitations_from_record(record: RepositoryValidationRecord) -> tuple[str, ...]:
    limitations: list[str] = []
    actual = record.actual or {}
    raw = actual.get("limitations")
    if isinstance(raw, list):
        limitations.extend(str(item) for item in raw if item is not None)
    if record.ai_executed:
        limitations.append("ai_executed=true (unexpected for validation harness)")
    if record.skip_reason:
        limitations.append(f"skip_reason={record.skip_reason}")
    if record.error_message:
        limitations.append(f"error={record.error_message}")
    # Deduplicate while preserving order.
    seen: set[str] = set()
    ordered: list[str] = []
    for item in limitations:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return tuple(ordered)


def _artifact_names(record: RepositoryValidationRecord) -> tuple[str, ...]:
    actual = record.actual or {}
    names = actual.get("artifact_names")
    if isinstance(names, list):
        return tuple(sorted(str(item) for item in names))
    return ()


def aggregate_false_positive_tracking(
    records: tuple[RepositoryValidationRecord, ...],
) -> FalsePositiveSummaryAggregate:
    """Aggregate FP tracking across repository records without changing Precision."""

    from codestrata.domain.quality_metrics.false_positives import (
        FalsePositiveRecord,
        merge_false_positive_records,
        summarize_false_positives,
    )

    collected: list[FalsePositiveRecord] = []
    for record in records:
        for item in record.false_positives:
            try:
                collected.append(FalsePositiveRecord.model_validate(item))
            except Exception:  # noqa: BLE001 — skip malformed historical rows
                continue
    merged = merge_false_positive_records(collected)
    counts = summarize_false_positives(merged)
    by_pack: dict[str, int] = {}
    by_rule: dict[str, int] = {}
    by_root: dict[str, int] = {}
    repos: set[str] = set()
    for item in merged:
        pack = item.assessment_area.split(":", 1)[0]
        by_pack[pack] = by_pack.get(pack, 0) + 1
        if item.rule_id:
            by_rule[item.rule_id] = by_rule.get(item.rule_id, 0) + 1
        if item.root_cause is not None:
            key = item.root_cause.value
            by_root[key] = by_root.get(key, 0) + 1
        repos.add(item.repository_id)
    return FalsePositiveSummaryAggregate(
        suspected=counts.suspected,
        confirmed=counts.confirmed,
        ambiguous=counts.ambiguous,
        expectation_errors=counts.expectation_errors,
        unsupported_capability=counts.unsupported_capability,
        rejected=counts.rejected,
        fixed=counts.fixed,
        open=counts.open,
        investigating=counts.investigating,
        total=counts.total,
        by_pack=dict(sorted(by_pack.items())),
        by_rule=dict(sorted(by_rule.items())),
        by_root_cause=dict(sorted(by_root.items())),
        affected_repository_ids=tuple(sorted(repos)),
        records=tuple(item.canonical_dict() for item in merged),
    )


def aggregate_false_negative_tracking(
    records: tuple[RepositoryValidationRecord, ...],
) -> FalseNegativeSummaryAggregate:
    """Aggregate FN tracking across repository records without changing Recall."""

    from codestrata.domain.quality_metrics.false_negatives import (
        FalseNegativeRecord,
        merge_false_negative_records,
        summarize_false_negatives,
    )

    collected: list[FalseNegativeRecord] = []
    for record in records:
        for item in getattr(record, "false_negatives", ()) or ():
            try:
                collected.append(FalseNegativeRecord.model_validate(item))
            except Exception:  # noqa: BLE001 — skip malformed historical rows
                continue
    merged = merge_false_negative_records(collected)
    counts = summarize_false_negatives(merged)
    by_pack: dict[str, int] = {}
    by_rule: dict[str, int] = {}
    by_root: dict[str, int] = {}
    repos: set[str] = set()
    for item in merged:
        pack = item.assessment_area.split(":", 1)[0]
        by_pack[pack] = by_pack.get(pack, 0) + 1
        rule_key = item.expected_rule_id or item.expected_signal_id or item.expected_entity_id
        if rule_key:
            by_rule[rule_key] = by_rule.get(rule_key, 0) + 1
        if item.root_cause is not None:
            key = item.root_cause.value
            by_root[key] = by_root.get(key, 0) + 1
        repos.add(item.repository_id)
    return FalseNegativeSummaryAggregate(
        suspected=counts.suspected,
        confirmed=counts.confirmed,
        ambiguous=counts.ambiguous,
        expectation_errors=counts.expectation_errors,
        unsupported_capability=counts.unsupported_capability,
        insufficient_evidence=counts.insufficient_evidence,
        rejected=counts.rejected,
        fixed=counts.fixed,
        open=counts.open,
        investigating=counts.investigating,
        total=counts.total,
        by_pack=dict(sorted(by_pack.items())),
        by_rule=dict(sorted(by_rule.items())),
        by_root_cause=dict(sorted(by_root.items())),
        affected_repository_ids=tuple(sorted(repos)),
        records=tuple(item.canonical_dict() for item in merged),
    )


def aggregate_pack_precision(
    records: tuple[RepositoryValidationRecord, ...],
) -> tuple[PackAggregateSummary, ...]:
    """Aggregate pack precision/recall using summed counts, never averaging percentages."""

    from codestrata.domain.quality_metrics.common import (
        QualityMetricSample,
        QualityMetricScope,
        QualityMetricSource,
        resolve_quality_metric_source,
        source_from_matrix_label,
    )
    from codestrata.domain.quality_metrics.precision import aggregate_precision_from_counts
    from codestrata.domain.quality_metrics.recall import aggregate_recall_from_counts

    summaries: list[PackAggregateSummary] = []
    for pack in CANONICAL_PACKS:
        tp = fp = fn = amb = 0
        evaluated = passed = failed = unavailable = 0
        source_ids: list[str] = []
        limitations: list[str] = []
        sources: list[QualityMetricSource] = []
        controlled = 0
        real_world = 0
        precision_positive_repos = 0
        expected_positive_repos = 0
        for record in records:
            pack_map = {item.pack: item for item in record.pack_precision}
            item = pack_map.get(pack)
            if record.verdict in {ValidationVerdict.SKIPPED, ValidationVerdict.ERROR}:
                if item is None:
                    limitations.append(
                        f"{record.repository_id}: excluded from precision/recall "
                        f"({record.verdict.value.lower()})"
                    )
                    continue
            if item is None:
                continue
            evaluated += 1
            source_ids.append(record.repository_id)
            tp += item.true_positives
            fp += item.false_positives
            fn += item.false_negatives
            amb += item.ambiguous
            if (item.true_positives + item.false_positives) > 0:
                precision_positive_repos += 1
            if (item.true_positives + item.false_negatives) > 0:
                expected_positive_repos += 1
            row = VALIDATION_MATRIX.get(record.repository_id) or {}
            src = source_from_matrix_label(row.get("controlled_vs_real_world"))
            sources.append(src)
            if src is QualityMetricSource.CONTROLLED_FIXTURE:
                controlled += 1
            elif src is QualityMetricSource.REAL_WORLD_REPOSITORY:
                real_world += 1
            if item.passed is True:
                passed += 1
            elif item.passed is False:
                failed += 1
            else:
                unavailable += 1
                limitations.append(
                    f"{record.repository_id}: pack precision passed=null (unavailable)"
                )
            if item.precision is None:
                limitations.append(f"{record.repository_id}: precision unavailable")
            if item.recall is None:
                limitations.append(f"{record.repository_id}: recall unavailable")

        source = resolve_quality_metric_source(sources)
        precision_sample = QualityMetricSample(
            repository_count=evaluated,
            positive_repository_count=precision_positive_repos,
            expected_positive_repository_count=expected_positive_repos,
            controlled_fixture_count=controlled,
            real_world_repository_count=real_world,
            ambiguous_count=amb,
            false_positive_count=fp,
            false_negative_count=fn,
        )
        recall_sample = QualityMetricSample(
            repository_count=evaluated,
            positive_repository_count=expected_positive_repos,
            expected_positive_repository_count=expected_positive_repos,
            controlled_fixture_count=controlled,
            real_world_repository_count=real_world,
            ambiguous_count=amb,
            false_positive_count=fp,
            false_negative_count=fn,
        )
        precision_metric = aggregate_precision_from_counts(
            scope=QualityMetricScope.VALIDATION_SET,
            scope_id=pack,
            true_positive_count=tp,
            false_positive_count=fp,
            source=source,
            sample=precision_sample,
            limitations=limitations,
        )
        recall_metric = aggregate_recall_from_counts(
            scope=QualityMetricScope.VALIDATION_SET,
            scope_id=pack,
            true_positive_count=tp,
            false_negative_count=fn,
            source=source,
            sample=recall_sample,
            limitations=limitations,
        )
        for note in (*precision_metric.limitations, *recall_metric.limitations):
            limitations.append(note)
        summaries.append(
            PackAggregateSummary(
                pack=pack,
                repositories_evaluated=evaluated,
                repositories_passed=passed,
                repositories_failed=failed,
                repositories_unavailable=unavailable,
                true_positives=tp,
                false_positives=fp,
                false_negatives=fn,
                ambiguous=amb,
                precision=precision_metric.as_compat_float(),
                recall=recall_metric.as_compat_float(),
                limitations=tuple(sorted(set(limitations))),
                source_repository_ids=tuple(sorted(set(source_ids))),
                precision_metric=precision_metric.canonical_dict(),
                precision_metric_id=precision_metric.metric_id,
                precision_availability=precision_metric.availability.value,
                precision_classification_status=(
                    precision_metric.classification_status.value
                ),
                sample=precision_sample.model_dump(mode="json"),
                precision_source=source.value,
                recall_metric=recall_metric.canonical_dict(),
                recall_metric_id=recall_metric.metric_id,
                recall_availability=recall_metric.availability.value,
                recall_classification_status=recall_metric.classification_status.value,
                recall_sample=recall_sample.model_dump(mode="json"),
                recall_source=source.value,
                expected_positive_repository_count=expected_positive_repos,
            )
        )
    return tuple(summaries)


def build_summary_artifact(
    loaded: tuple[tuple[RepositoryValidationRecord, SourceRecordRef], ...],
    *,
    scope: SummaryScope,
    scope_label: str | None = None,
    generated_at: str | None = None,
) -> ValidationSummaryArtifact:
    """Assemble the permanent summary artifact from validated records."""

    records = tuple(record for record, _ref in loaded)
    refs = tuple(ref for _record, ref in loaded)

    rows: list[RepositorySummaryRow] = []
    mismatches: list[MismatchSummaryEntry] = []
    mismatches_by_area: dict[str, int] = {}
    verdict_totals = VerdictTotals()
    evaluated = matched = 0
    without_eval = 0

    passed = failed = errors = skipped = 0
    for record, ref in loaded:
        if record.verdict == ValidationVerdict.PASS:
            passed += 1
        elif record.verdict == ValidationVerdict.FAIL:
            failed += 1
        elif record.verdict == ValidationVerdict.ERROR:
            errors += 1
        elif record.verdict == ValidationVerdict.SKIPPED:
            skipped += 1

        evaluated += record.expectations_evaluated
        matched += record.expectations_matched
        if record.expectations_evaluated == 0 and record.verdict in {
            ValidationVerdict.ERROR,
            ValidationVerdict.SKIPPED,
        }:
            without_eval += 1

        mismatch_count = len(record.mismatches)
        for mismatch in record.mismatches:
            area = mismatch.assessment_area
            mismatches_by_area[area] = mismatches_by_area.get(area, 0) + 1
            mismatches.append(
                MismatchSummaryEntry(
                    repository_id=record.repository_id,
                    assessment_area=area,
                    expectation=_bound(mismatch.expectation),
                    actual=_bound(mismatch.actual),
                    diagnostic=_bound(mismatch.diagnostic),
                    source_record=ref,
                )
            )

        rows.append(
            RepositorySummaryRow(
                repository_id=record.repository_id,
                run_id=record.run_id,
                verdict=record.verdict.value,
                source_identity=_source_identity(record.repository_id),
                expectations_evaluated=record.expectations_evaluated,
                expectations_matched=record.expectations_matched,
                mismatch_count=mismatch_count,
                pack_precision=tuple(
                    item.model_dump(mode="json") for item in record.pack_precision
                ),
                error_message=record.error_message,
                skip_reason=record.skip_reason,
                source_record=ref,
                assessment_artifact_names=_artifact_names(record),
                limitations=_limitations_from_record(record),
                assessment_schema_version=record.schema_version,
                ai_executed=record.ai_executed,
            )
        )

    rows_sorted = tuple(sorted(rows, key=lambda item: item.repository_id))
    mismatches_sorted = tuple(
        sorted(
            mismatches,
            key=lambda item: (
                item.assessment_area,
                item.repository_id,
                item.diagnostic,
                item.expectation,
            ),
        )
    )
    pack_summaries = aggregate_pack_precision(records)
    coverage_gaps = derive_coverage_gaps(records=records, pack_summaries=pack_summaries)
    fp_tracking = aggregate_false_positive_tracking(records)
    fn_tracking = aggregate_false_negative_tracking(records)

    unavailable: list[str] = []
    for pack in pack_summaries:
        if pack.precision is None:
            unavailable.append(f"{pack.pack}.precision")
        if pack.recall is None:
            unavailable.append(f"{pack.pack}.recall")
        if pack.repositories_evaluated == 0:
            unavailable.append(f"{pack.pack}.unevaluated")

    limitations = [
        DISCLAIMER,
        "Summary is derived only from Slice 4.11 RepositoryValidationRecord artifacts.",
        "Coverage gaps are informational and are not automatic failures.",
        "Remote network SKIPPED verdicts are not treated as accuracy failures.",
        "False-positive tracking is internal validation metadata; PrecisionMetric "
        "continues to use pack classifier FP counts unchanged.",
        "False-negative tracking is internal validation metadata; RecallMetric "
        "continues to use pack classifier FN counts unchanged.",
    ]
    if scope == SummaryScope.LATEST_PER_REPOSITORY:
        limitations.append(
            "Scope is latest-per-repository; records may originate from different "
            "suite executions and are not one atomic suite run."
        )

    summary_run_id = deterministic_summary_run_id(refs)
    overall = derive_overall_verdict(tuple(item.verdict for item in records))
    label = scope_label or scope.value

    return ValidationSummaryArtifact(
        summary_schema_version=SUMMARY_SCHEMA_VERSION,
        generated_from_record_schema_version=RECORD_SCHEMA_VERSION,
        summary_run_id=summary_run_id,
        scope=scope,
        scope_label=label,
        repository_count=len(rows_sorted),
        repositories=rows_sorted,
        verdict_totals=VerdictTotals(
            passed=passed,
            failed=failed,
            errors=errors,
            skipped=skipped,
        ),
        expectation_totals=ExpectationTotals(
            evaluated=evaluated,
            matched=matched,
            mismatched=evaluated - matched,
            repositories_without_evaluation=without_eval,
        ),
        mismatch_totals=len(mismatches_sorted),
        mismatches_by_area=dict(sorted(mismatches_by_area.items())),
        mismatches=mismatches_sorted,
        pack_precision=pack_summaries,
        false_positive_tracking=fp_tracking,
        false_negative_tracking=fn_tracking,
        unavailable_metrics=tuple(sorted(set(unavailable))),
        coverage_gaps=coverage_gaps,
        source_record_refs=tuple(
            sorted(refs, key=lambda item: (item.repository_id, item.run_id))
        ),
        overall_verdict=overall,
        limitations=tuple(sorted(set(limitations))),
        disclaimer=DISCLAIMER,
        generated_at=generated_at
        or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def deterministic_summary_run_id(refs: tuple[SourceRecordRef, ...]) -> str:
    """Stable id from sorted repository/run pairs (no wall-clock dependency)."""

    material = "\n".join(
        f"{item.repository_id}:{item.run_id}:{item.relative_path}"
        for item in sorted(refs, key=lambda r: (r.repository_id, r.run_id, r.relative_path))
    )
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]
    return f"s-{digest}"


def _bound(text: str, *, limit: int = 240) -> str:
    value = " ".join(str(text).split())
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def render_summary_markdown(artifact: ValidationSummaryArtifact) -> str:
    """Engineering-facing Markdown summary (deterministic)."""

    lines: list[str] = [
        "# CodeStrata Assessment Accuracy Validation",
        "",
        "## Scope",
        "",
        f"- Scope: `{artifact.scope_label}`",
        f"- Summary schema: `{artifact.summary_schema_version}`",
        f"- Record schema: `{artifact.generated_from_record_schema_version}`",
        f"- Summary run id: `{artifact.summary_run_id}`",
        f"- Repositories: {artifact.repository_count}",
        "",
        f"> {artifact.disclaimer}",
        "",
        "## Overall Verdict",
        "",
        f"**{artifact.overall_verdict.value}**",
        "",
        (
            f"PASS={artifact.verdict_totals.passed} "
            f"FAIL={artifact.verdict_totals.failed} "
            f"ERROR={artifact.verdict_totals.errors} "
            f"SKIPPED={artifact.verdict_totals.skipped}"
        ),
        "",
        (
            f"Expectations matched "
            f"{artifact.expectation_totals.matched}/"
            f"{artifact.expectation_totals.evaluated} "
            f"(mismatched={artifact.expectation_totals.mismatched})"
        ),
        "",
        "## Repository Results",
        "",
        "| Repository | Run ID | Verdict | Matched | Mismatches | Source record |",
        "|---|---|---|---:|---:|---|",
    ]
    for row in artifact.repositories:
        lines.append(
            f"| {row.repository_id} | `{row.run_id}` | {row.verdict} | "
            f"{row.expectations_matched}/{row.expectations_evaluated} | "
            f"{row.mismatch_count} | `{row.source_record.relative_path}` |"
        )
        if row.error_message:
            lines.append(f"|  |  | error |  |  | {_md_escape(row.error_message)} |")
        if row.skip_reason:
            lines.append(f"|  |  | skip |  |  | {_md_escape(row.skip_reason)} |")

    lines.extend(
        [
            "",
            "## Pack Accuracy",
            "",
            "| Pack | TP | FP | FN | Precision | Recall | Validation scope |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for pack in artifact.pack_precision:
        lines.append(
            f"| {pack.pack} | "
            f"{pack.true_positives} | {pack.false_positives} | "
            f"{pack.false_negatives} | "
            f"{_fmt_precision_with_note(pack)} | {_fmt_recall_with_note(pack)} | "
            f"{_fmt_validation_scope(pack)} |"
        )

    lines.extend(
        [
            "",
            "## False-Positive Tracking",
            "",
            "Internal validation lifecycle only. PrecisionMetric pack FP counts are unchanged.",
            "",
        ]
    )
    tracking = artifact.false_positive_tracking
    if tracking is None or tracking.total == 0:
        lines.append("No tracked false positives in selected records.")
    else:
        lines.extend(
            [
                (
                    f"Suspected={tracking.suspected} Confirmed={tracking.confirmed} "
                    f"Ambiguous={tracking.ambiguous} ExpectationErrors="
                    f"{tracking.expectation_errors} Fixed={tracking.fixed} "
                    f"Open={tracking.open}"
                ),
                "",
                "| ID | Repository | Area | Rule/Entity | Classification | Status | Root Cause | First Seen | Last Seen |",
                "|---|---|---|---|---|---|---|---|---|",
            ]
        )
        for item in tracking.records:
            lines.append(
                f"| `{item.get('false_positive_id', '')}` | "
                f"{item.get('repository_id', '')} | "
                f"{item.get('assessment_area', '')} | "
                f"{item.get('rule_id') or item.get('entity_id') or ''} | "
                f"{item.get('classification', '')} | "
                f"{item.get('status', '')} | "
                f"{item.get('root_cause') or ''} | "
                f"`{item.get('first_seen_run_id', '')}` | "
                f"`{item.get('last_seen_run_id', '')}` |"
            )

    lines.extend(
        [
            "",
            "## False-Negative Tracking",
            "",
            "Internal validation lifecycle only. RecallMetric pack FN counts are unchanged.",
            "",
        ]
    )
    fn_tracking = artifact.false_negative_tracking
    if fn_tracking is None or fn_tracking.total == 0:
        lines.append("No tracked false negatives in selected records.")
    else:
        lines.extend(
            [
                (
                    f"Suspected={fn_tracking.suspected} Confirmed={fn_tracking.confirmed} "
                    f"Ambiguous={fn_tracking.ambiguous} ExpectationErrors="
                    f"{fn_tracking.expectation_errors} Unsupported="
                    f"{fn_tracking.unsupported_capability} InsufficientEvidence="
                    f"{fn_tracking.insufficient_evidence} Fixed={fn_tracking.fixed} "
                    f"Open={fn_tracking.open}"
                ),
                "",
                "| ID | Repository | Area | Expected Rule/Entity | Classification | Status | Root Cause | First Seen | Last Seen |",
                "|---|---|---|---|---|---|---|---|---|",
            ]
        )
        for item in fn_tracking.records:
            expected_ref = (
                item.get("expected_rule_id")
                or item.get("expected_signal_id")
                or item.get("expected_entity_id")
                or item.get("expected_subject")
                or ""
            )
            lines.append(
                f"| `{item.get('false_negative_id', '')}` | "
                f"{item.get('repository_id', '')} | "
                f"{item.get('assessment_area', '')} | "
                f"{expected_ref} | "
                f"{item.get('classification', '')} | "
                f"{item.get('status', '')} | "
                f"{item.get('root_cause') or ''} | "
                f"`{item.get('first_seen_run_id', '')}` | "
                f"`{item.get('last_seen_run_id', '')}` |"
            )

    lines.extend(["", "## Mismatches", ""])
    if not artifact.mismatches:
        lines.append("No mismatches.")
    else:
        lines.append("| Area | Repository | Diagnostic |")
        lines.append("|---|---|---|")
        for item in artifact.mismatches:
            lines.append(
                f"| {item.assessment_area} | {item.repository_id} | "
                f"{_md_escape(item.diagnostic)} |"
            )

    lines.extend(["", "## Coverage Gaps", ""])
    if not artifact.coverage_gaps:
        lines.append("No coverage gaps recorded.")
    else:
        for gap in artifact.coverage_gaps:
            lines.append(f"- `{gap.gap_id}` ({gap.category}): {gap.description}")

    lines.extend(["", "## Limitations", ""])
    for item in artifact.limitations:
        lines.append(f"- {item}")

    lines.extend(["", "## Source Records", ""])
    for ref in artifact.source_record_refs:
        lines.append(f"- `{ref.relative_path}` (run `{ref.run_id}`)")

    lines.append("")
    return "\n".join(lines)


def _fmt_metric(value: float | None) -> str:
    if value is None:
        return "unavailable"
    return f"{value:.6f}".rstrip("0").rstrip(".")


def _fmt_precision_with_note(pack: PackAggregateSummary) -> str:
    """Render precision without claiming product-wide accuracy."""

    from codestrata.domain.quality_metrics.precision import format_precision_display

    if pack.precision is None:
        return "unavailable"
    display = format_precision_display(pack.precision)
    return f"{display} within this validation scope"


def _fmt_recall_with_note(pack: PackAggregateSummary) -> str:
    """Render recall without claiming product-wide detection."""

    from codestrata.domain.quality_metrics.recall import format_recall_display

    if pack.recall is None:
        return "unavailable"
    display = format_recall_display(pack.recall)
    return f"{display} within this authored validation scope"


def _fmt_validation_scope(pack: PackAggregateSummary) -> str:
    source = pack.recall_source or pack.precision_source or ""
    sample = pack.recall_sample or pack.sample or {}
    notes: list[str] = []
    if source == "controlled_fixture":
        notes.append("Controlled fixtures")
    elif source == "real_world_repository":
        notes.append("Real-world repositories")
    elif source == "mixed_validation_set":
        controlled = sample.get("controlled_fixture_count", 0)
        real = sample.get("real_world_repository_count", 0)
        notes.append(f"Controlled={controlled} + real-world={real}")
    else:
        notes.append("Expected/actual validation")
    expected_repos = pack.expected_positive_repository_count
    if expected_repos:
        notes.append(f"expected-positive repos={expected_repos}")
    else:
        notes.append("no authored expected positives in aggregate")
    if pack.precision is None and pack.recall is None:
        notes.append("precision/recall unavailable")
    elif pack.recall is None:
        notes.append("recall unavailable")
    elif pack.recall_classification_status == "provisional":
        notes.append("provisional recall sample")
    return "; ".join(notes)


def _fmt_availability(pack: PackAggregateSummary) -> str:
    availability = pack.precision_availability or (
        "unavailable" if pack.precision is None else "available"
    )
    source = pack.precision_source or ""
    sample = pack.sample or {}
    notes: list[str] = [availability]
    if source == "controlled_fixture":
        notes.append("controlled fixtures")
    elif source == "real_world_repository":
        notes.append("real-world repositories")
    elif source == "mixed_validation_set":
        controlled = sample.get("controlled_fixture_count", 0)
        real = sample.get("real_world_repository_count", 0)
        notes.append(f"controlled={controlled} + real-world={real}")
    if pack.precision_classification_status == "provisional":
        notes.append("provisional sample")
    return "; ".join(notes)


def _md_escape(value: str) -> str:
    return value.replace("|", "\\|")


def write_summary_artifacts(
    artifact: ValidationSummaryArtifact,
    *,
    records_root: Path = RESULTS_DIR,
    update_latest: bool = True,
    write_json: bool = True,
    write_markdown: bool = True,
) -> Path:
    """Persist summary under ``{records_root}/summaries/`` without touching repo records."""

    summaries_root = records_root / "summaries"
    run_dir = summaries_root / "runs" / artifact.summary_run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_bundle(
        run_dir,
        artifact,
        write_json=write_json,
        write_markdown=write_markdown,
    )
    if update_latest:
        latest_dir = summaries_root / "latest"
        latest_dir.mkdir(parents=True, exist_ok=True)
        _write_bundle(
            latest_dir,
            artifact,
            write_json=write_json,
            write_markdown=write_markdown,
        )
        (summaries_root / "latest_summary_run_id.txt").write_text(
            artifact.summary_run_id + "\n",
            encoding="utf-8",
        )
    return run_dir


def _write_bundle(
    directory: Path,
    artifact: ValidationSummaryArtifact,
    *,
    write_json: bool,
    write_markdown: bool,
) -> None:
    if write_json:
        payload = artifact.model_dump(mode="json")
        (directory / "validation-summary.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if write_markdown:
        (directory / "validation-summary.md").write_text(
            render_summary_markdown(artifact),
            encoding="utf-8",
        )


def generate_summary_from_records(
    *,
    records_root: Path = RESULTS_DIR,
    repository_ids: set[str] | None = None,
    run_ids: Mapping[str, str] | None = None,
    update_latest: bool = True,
    write_json: bool = True,
    write_markdown: bool = True,
    require_all_requested: bool = False,
) -> tuple[ValidationSummaryArtifact, Path]:
    """Load records, build artifact, write JSON/Markdown. No assessment execution."""

    if run_ids:
        scope = SummaryScope.EXPLICIT_RUN_IDS
        label = "explicit-run-ids"
        require_all_requested = True
    elif repository_ids is not None:
        scope = SummaryScope.FILTERED_LATEST
        label = "filtered-latest"
    else:
        scope = SummaryScope.LATEST_PER_REPOSITORY
        label = "latest-per-repository"

    loaded = load_records_for_summary(
        records_root=records_root,
        repository_ids=repository_ids,
        run_ids=run_ids,
        prefer_latest=True,
        require_all_requested=require_all_requested,
    )
    if not loaded:
        raise RecordValidationError("no validation records available to summarize")

    artifact = build_summary_artifact(loaded, scope=scope, scope_label=label)
    out_dir = write_summary_artifacts(
        artifact,
        records_root=records_root,
        update_latest=update_latest,
        write_json=write_json,
        write_markdown=write_markdown,
    )
    return artifact, out_dir
