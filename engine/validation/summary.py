"""Validation summary helpers."""

from __future__ import annotations

from validation.compare import safe_artifact_path
from validation.models import ValidationRunResult, ValidationSummary, ValidationVerdict
from validation.paths import VALIDATION_ROOT


def build_validation_summary(
    results: tuple[ValidationRunResult, ...] | list[ValidationRunResult],
) -> ValidationSummary:
    results_tuple = tuple(results)
    mismatches_by_area: dict[str, int] = {}
    durations: dict[str, float] = {}
    artifacts: dict[str, str] = {}
    total_expectations = 0
    matched_expectations = 0
    passed = failed = errors = skipped = 0

    for result in results_tuple:
        if result.verdict == ValidationVerdict.PASS:
            passed += 1
        elif result.verdict == ValidationVerdict.FAIL:
            failed += 1
        elif result.verdict == ValidationVerdict.ERROR:
            errors += 1
        elif result.verdict == ValidationVerdict.SKIPPED:
            skipped += 1

        total_expectations += result.expectations_evaluated
        matched_expectations += result.expectations_matched
        if result.duration_ms is not None:
            durations[result.repository_id] = result.duration_ms
        if result.artifact_dir:
            artifacts[result.repository_id] = safe_artifact_path(
                result.artifact_dir,
                base=VALIDATION_ROOT,
            )
        elif result.record_dir:
            artifacts[result.repository_id] = result.record_dir
        for mismatch in result.mismatches:
            mismatches_by_area[mismatch.assessment_area] = (
                mismatches_by_area.get(mismatch.assessment_area, 0) + 1
            )

    return ValidationSummary(
        total_repositories=len(results_tuple),
        passed=passed,
        failed=failed,
        errors=errors,
        skipped=skipped,
        total_expectations=total_expectations,
        matched_expectations=matched_expectations,
        mismatches_by_area=dict(sorted(mismatches_by_area.items())),
        repository_durations_ms=durations,
        artifact_locations=artifacts,
        results=results_tuple,
    )


def summary_to_safe_dict(summary: ValidationSummary) -> dict:
    """JSON-serializable summary without absolute user paths or source bodies."""

    payload = summary.model_dump(mode="json")
    # Durations are retained for operator diagnostics but marked volatile for
    # determinism comparisons elsewhere.
    for result in payload.get("results", []):
        result.pop("duration_ms", None)
        if result.get("artifact_dir"):
            result["artifact_dir"] = safe_artifact_path(
                result["artifact_dir"],
                base=VALIDATION_ROOT,
            )
        if result.get("record_dir"):
            result["record_dir"] = safe_artifact_path(
                result["record_dir"],
                base=VALIDATION_ROOT,
            )
        for mismatch in result.get("mismatches") or []:
            if mismatch.get("artifact_path"):
                mismatch["artifact_path"] = safe_artifact_path(
                    mismatch["artifact_path"],
                    base=VALIDATION_ROOT,
                )
    return payload
