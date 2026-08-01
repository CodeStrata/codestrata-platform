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


def aggregate_pack_precision(
    records: tuple[RepositoryValidationRecord, ...],
) -> tuple[PackAggregateSummary, ...]:
    """Aggregate pack precision using sum(TP/FP/FN), never averaging percentages."""

    summaries: list[PackAggregateSummary] = []
    for pack in CANONICAL_PACKS:
        tp = fp = fn = amb = 0
        evaluated = passed = failed = unavailable = 0
        source_ids: list[str] = []
        limitations: list[str] = []
        for record in records:
            pack_map = {item.pack: item for item in record.pack_precision}
            item = pack_map.get(pack)
            if item is None:
                continue
            evaluated += 1
            source_ids.append(record.repository_id)
            tp += item.true_positives
            fp += item.false_positives
            fn += item.false_negatives
            amb += item.ambiguous
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

        precision, recall, reason = compute_precision_recall(
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
        )
        if reason:
            limitations.append(reason)
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
                precision=precision,
                recall=recall,
                limitations=tuple(sorted(set(limitations))),
                source_repository_ids=tuple(sorted(set(source_ids))),
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
            "| Pack | Repos | TP | FP | FN | Amb | Precision | Recall |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for pack in artifact.pack_precision:
        lines.append(
            f"| {pack.pack} | {pack.repositories_evaluated} | "
            f"{pack.true_positives} | {pack.false_positives} | "
            f"{pack.false_negatives} | {pack.ambiguous} | "
            f"{_fmt_metric(pack.precision)} | {_fmt_metric(pack.recall)} |"
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
