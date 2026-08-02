"""Orchestrate multi-repository validation runs."""

from __future__ import annotations

import shutil
import tempfile
import time
from pathlib import Path

from validation.actual import run_real_assessment
from validation.compare import compare_actual_to_expected, safe_artifact_path
from validation.models import (
    ComparisonOutcome,
    ExpectedResults,
    ValidationRepository,
    ValidationRunResult,
    ValidationVerdict,
)
from validation.paths import RESULTS_DIR, VALIDATION_ROOT, resolve_local_path
from validation.recording import (
    build_repository_validation_record,
    new_run_id,
    write_repository_validation_record,
)
from validation.registry import RegistryError, resolve_expected_results
from validation.remote import RemoteRepositoryError, prepare_remote_repository


def run_repository_validation(
    definition: ValidationRepository,
    *,
    output_root: Path,
    keep_results: bool = False,
    include_remote: bool = False,
    local_only: bool = False,
    validation_root: Path = VALIDATION_ROOT,
    records_root: Path | None = None,
    record_results: bool = True,
) -> ValidationRunResult:
    """Run assessment + comparison for one repository definition.

    Always writes a permanent Slice 4.11 validation record under
    ``records_root/{repository_id}/`` (default: ``validation/results/``)
    when ``record_results`` is true. Assessment outputs under
    ``output_root/{repository_id}/assessment-output/`` are retained only when
    ``keep_results`` is true.
    """

    started = time.perf_counter()
    work_dirs: list[Path] = []
    artifact_dir = output_root / definition.repository_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    effective_records_root = records_root if records_root is not None else RESULTS_DIR
    run_id = new_run_id()
    expected: ExpectedResults | None = None
    record_dir_str: str | None = None

    def _record(
        *,
        verdict: ValidationVerdict,
        outcome: ComparisonOutcome | None = None,
        actual=None,
        ai_executed: bool = False,
        error_message: str | None = None,
        skip_reason: str | None = None,
    ) -> str | None:
        nonlocal record_dir_str
        if not record_results:
            return None
        try:
            effective_records_root.mkdir(parents=True, exist_ok=True)
            record = build_repository_validation_record(
                repository_id=definition.repository_id,
                run_id=run_id,
                verdict=verdict,
                expected=expected,
                actual=actual,
                outcome=outcome,
                ai_executed=ai_executed,
                error_message=error_message,
                skip_reason=skip_reason,
                records_root=effective_records_root,
            )
            written = write_repository_validation_record(
                record,
                records_root=effective_records_root,
                update_latest=True,
            )
            record_dir_str = safe_artifact_path(written, base=VALIDATION_ROOT)
            return record_dir_str
        except Exception:  # noqa: BLE001 - recording must not mask harness verdicts
            return None

    try:
        if not definition.enabled:
            _record(
                verdict=ValidationVerdict.SKIPPED,
                skip_reason="repository disabled",
            )
            return ValidationRunResult(
                repository_id=definition.repository_id,
                verdict=ValidationVerdict.SKIPPED,
                skip_reason="repository disabled",
                duration_ms=_elapsed_ms(started),
                artifact_dir=_safe_dir(artifact_dir, keep_results),
                record_dir=record_dir_str,
            )

        if definition.source_type.value == "remote":
            if local_only or not include_remote:
                skip_reason = (
                    "remote repository excluded by mode "
                    f"(local_only={local_only}, include_remote={include_remote})"
                )
                _record(verdict=ValidationVerdict.SKIPPED, skip_reason=skip_reason)
                return ValidationRunResult(
                    repository_id=definition.repository_id,
                    verdict=ValidationVerdict.SKIPPED,
                    skip_reason=skip_reason,
                    duration_ms=_elapsed_ms(started),
                    artifact_dir=_safe_dir(artifact_dir, keep_results),
                    record_dir=record_dir_str,
                )
            clone_root = Path(tempfile.mkdtemp(prefix="codestrata-validation-clone-"))
            work_dirs.append(clone_root)
            try:
                repo_path = prepare_remote_repository(definition, clone_root=clone_root)
            except RemoteRepositoryError as exc:
                skip_reason = f"remote unavailable: {exc}"
                _record(verdict=ValidationVerdict.SKIPPED, skip_reason=skip_reason)
                return ValidationRunResult(
                    repository_id=definition.repository_id,
                    verdict=ValidationVerdict.SKIPPED,
                    skip_reason=skip_reason,
                    duration_ms=_elapsed_ms(started),
                    artifact_dir=_safe_dir(artifact_dir, keep_results),
                    record_dir=record_dir_str,
                )
        else:
            if definition.local_path is None:
                raise RegistryError("local repository missing local_path")
            repo_path = resolve_local_path(
                definition.local_path,
                validation_root=validation_root,
            )
            if not repo_path.is_dir():
                skip_reason = f"local path missing: {definition.local_path}"
                _record(verdict=ValidationVerdict.SKIPPED, skip_reason=skip_reason)
                return ValidationRunResult(
                    repository_id=definition.repository_id,
                    verdict=ValidationVerdict.SKIPPED,
                    skip_reason=skip_reason,
                    duration_ms=_elapsed_ms(started),
                    artifact_dir=_safe_dir(artifact_dir, keep_results),
                    record_dir=record_dir_str,
                )

        expected = resolve_expected_results(definition, validation_root=validation_root)
        config_path = None
        if definition.assessment_config:
            config_candidate = validation_root / definition.assessment_config
            if not config_candidate.is_file():
                raise RegistryError(
                    f"assessment_config not found: {definition.assessment_config}"
                )
            config_path = config_candidate

        run_output = artifact_dir / "assessment-output"
        if run_output.exists():
            shutil.rmtree(run_output)
        run_output.mkdir(parents=True, exist_ok=True)

        try:
            actual, report_path = run_real_assessment(
                repository_path=repo_path,
                output_directory=run_output,
                config_path=config_path,
            )
        except Exception as exc:  # noqa: BLE001 - classify as ERROR verdict
            _record(
                verdict=ValidationVerdict.ERROR,
                error_message=str(exc),
            )
            return ValidationRunResult(
                repository_id=definition.repository_id,
                verdict=ValidationVerdict.ERROR,
                error_message=str(exc),
                duration_ms=_elapsed_ms(started),
                artifact_dir=_safe_dir(artifact_dir, keep_results),
                record_dir=record_dir_str,
            )

        outcome = compare_actual_to_expected(
            repository_id=definition.repository_id,
            expected=expected,
            actual=actual,
            artifact_path=safe_artifact_path(report_path, base=artifact_dir),
            run_id=run_id,
        )
        verdict = (
            ValidationVerdict.PASS if not outcome.mismatches else ValidationVerdict.FAIL
        )
        _record(
            verdict=verdict,
            outcome=outcome,
            actual=actual,
            ai_executed=bool(actual.ai_executed),
        )
        return ValidationRunResult(
            repository_id=definition.repository_id,
            verdict=verdict,
            mismatches=outcome.mismatches,
            duration_ms=_elapsed_ms(started),
            artifact_dir=_safe_dir(artifact_dir, keep_results),
            record_dir=record_dir_str,
            expectations_evaluated=outcome.expectations_evaluated,
            expectations_matched=outcome.expectations_matched,
            ai_executed=actual.ai_executed,
        )
    except Exception as exc:  # noqa: BLE001 - harness failure
        _record(
            verdict=ValidationVerdict.ERROR,
            error_message=str(exc),
        )
        return ValidationRunResult(
            repository_id=definition.repository_id,
            verdict=ValidationVerdict.ERROR,
            error_message=str(exc),
            duration_ms=_elapsed_ms(started),
            artifact_dir=_safe_dir(artifact_dir, keep_results),
            record_dir=record_dir_str,
        )
    finally:
        if not keep_results:
            for path in work_dirs:
                shutil.rmtree(path, ignore_errors=True)
            # Remove assessment outputs only — permanent records live under
            # records_root and must survive cleanup.
            assessment_output = artifact_dir / "assessment-output"
            if assessment_output.exists():
                shutil.rmtree(assessment_output, ignore_errors=True)
            # Drop empty per-repo assessment container under output_root.
            if artifact_dir.exists() and not any(artifact_dir.iterdir()):
                shutil.rmtree(artifact_dir, ignore_errors=True)


def run_validation_suite(
    definitions: tuple[ValidationRepository, ...] | list[ValidationRepository],
    *,
    output_root: Path,
    keep_results: bool = False,
    include_remote: bool = False,
    local_only: bool = False,
    fail_fast: bool = False,
    validation_root: Path = VALIDATION_ROOT,
    records_root: Path | None = None,
    record_results: bool = True,
) -> tuple[ValidationRunResult, ...]:
    results: list[ValidationRunResult] = []
    for definition in definitions:
        result = run_repository_validation(
            definition,
            output_root=output_root,
            keep_results=keep_results,
            include_remote=include_remote,
            local_only=local_only,
            validation_root=validation_root,
            records_root=records_root,
            record_results=record_results,
        )
        results.append(result)
        if fail_fast and result.verdict in {
            ValidationVerdict.FAIL,
            ValidationVerdict.ERROR,
        }:
            break
    return tuple(results)


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000.0, 3)


def _safe_dir(artifact_dir: Path, keep_results: bool) -> str | None:
    if not keep_results:
        return None
    return str(artifact_dir)
