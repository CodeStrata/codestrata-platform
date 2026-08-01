"""Permanent per-repository validation records (Epic 4 Slice 4.11).

Every repository execution writes a canonical comparison record containing
expected results, actual results, comparison outcome, pack precision/recall,
mismatches, and verdict. These records are the history surface for Slice 4.12.

Records are written under ``validation/results/{repository_id}/`` (gitignored).
Assessment outputs remain optional via ``--keep-results``.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from validation.models import (
    ActualAssessmentResult,
    ComparisonMismatch,
    ComparisonOutcome,
    ExpectedResults,
    PackPrecisionRecord,
    ValidationVerdict,
)
from validation.paths import RESULTS_DIR, VALIDATION_ROOT

RECORD_SCHEMA_VERSION = "1.0"
# Base form YYYYMMDDTHHMMSSZ; optional _N suffix when two runs share a second.
_RUN_ID_RE = re.compile(r"^\d{8}T\d{6}Z(?:_\d+)?$")

# Re-export for callers that import recording types from this module.
__all__ = [
    "RECORD_SCHEMA_VERSION",
    "ComparisonOutcome",
    "PackPrecisionRecord",
    "RepositoryValidationRecord",
    "build_repository_validation_record",
    "expected_for_recording",
    "actual_for_recording",
    "comparison_for_recording",
    "list_run_ids",
    "load_repository_validation_record",
    "new_run_id",
    "write_repository_validation_record",
]


class RepositoryValidationRecord(BaseModel):
    """Canonical per-repository validation evidence for one execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    record_schema_version: str = RECORD_SCHEMA_VERSION
    repository_id: str
    run_id: str
    recorded_at: str
    verdict: ValidationVerdict
    schema_version: str | None = None
    ai_executed: bool = False
    expectations_evaluated: int = 0
    expectations_matched: int = 0
    expected: dict[str, Any] = Field(default_factory=dict)
    actual: dict[str, Any] = Field(default_factory=dict)
    comparison: dict[str, Any] = Field(default_factory=dict)
    pack_precision: tuple[PackPrecisionRecord, ...] = ()
    mismatches: tuple[ComparisonMismatch, ...] = ()
    error_message: str | None = None
    skip_reason: str | None = None
    record_dir: str | None = None


def new_run_id(*, when: datetime | None = None) -> str:
    """UTC run id ``YYYYMMDDTHHMMSSZ`` (filesystem-safe, sortable)."""

    moment = when or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    else:
        moment = moment.astimezone(timezone.utc)
    return moment.strftime("%Y%m%dT%H%M%SZ")


def repository_records_root(
    repository_id: str,
    *,
    records_root: Path = RESULTS_DIR,
) -> Path:
    return records_root / repository_id


def run_record_dir(
    repository_id: str,
    run_id: str,
    *,
    records_root: Path = RESULTS_DIR,
) -> Path:
    if not _RUN_ID_RE.match(run_id):
        raise ValueError(f"invalid run_id: {run_id!r}")
    return repository_records_root(repository_id, records_root=records_root) / "runs" / run_id


def expected_for_recording(expected: ExpectedResults) -> dict[str, Any]:
    """Serialize expected results without absolute paths."""

    return expected.model_dump(mode="json")


def actual_for_recording(actual: ActualAssessmentResult) -> dict[str, Any]:
    """Serialize comparison-relevant actuals without source bodies or abs paths."""

    # Local import avoids compare ↔ recording ↔ actual cycles at module load.
    from validation.actual import normalized_for_determinism

    payload = normalized_for_determinism(actual)
    payload["security_findings"] = [
        item.model_dump(mode="json") for item in actual.security_findings
    ]
    payload["architecture_findings"] = [
        item.model_dump(mode="json") for item in actual.architecture_findings
    ]
    if actual.architecture_graph is not None:
        payload["architecture_graph"] = actual.architecture_graph.model_dump(mode="json")
    payload["technical_debt_findings"] = [
        item.model_dump(mode="json") for item in actual.technical_debt_findings
    ]
    payload["dependency_findings"] = [
        item.model_dump(mode="json") for item in actual.dependency_findings
    ]
    payload["dependency_manifests"] = [
        item.model_dump(mode="json") for item in actual.dependency_manifests
    ]
    payload["cloud_findings"] = [
        item.model_dump(mode="json") for item in actual.cloud_findings
    ]
    payload["cloud_signals"] = [
        item.model_dump(mode="json") for item in actual.cloud_signals
    ]
    payload["cloud_recommendations"] = [
        item.model_dump(mode="json") for item in actual.cloud_recommendations
    ]
    payload["ai_readiness_findings"] = [
        item.model_dump(mode="json") for item in actual.ai_readiness_findings
    ]
    payload["ai_readiness_signals"] = [
        item.model_dump(mode="json") for item in actual.ai_readiness_signals
    ]
    payload["ai_readiness_recommendations"] = [
        item.model_dump(mode="json") for item in actual.ai_readiness_recommendations
    ]
    payload["modernization_recommendations"] = [
        item.model_dump(mode="json") for item in actual.modernization_recommendations
    ]
    payload["modernization_priority_actions"] = [
        item.model_dump(mode="json") for item in actual.modernization_priority_actions
    ]
    payload["modernization_roadmap_initiatives"] = [
        item.model_dump(mode="json") for item in actual.modernization_roadmap_initiatives
    ]
    # Relativize artifact path keys only (values may be absolute at runtime).
    payload["artifact_names"] = sorted(actual.artifact_paths.keys())
    return payload


def comparison_for_recording(
    *,
    outcome: ComparisonOutcome,
    verdict: ValidationVerdict,
) -> dict[str, Any]:
    """Serialize comparison outcome for permanent storage."""

    mismatches = [
        {
            **item.model_dump(mode="json"),
            "artifact_path": (
                _safe_record_path(item.artifact_path) if item.artifact_path else None
            ),
        }
        for item in outcome.mismatches
    ]
    return {
        "verdict": verdict.value,
        "expectations_evaluated": outcome.expectations_evaluated,
        "expectations_matched": outcome.expectations_matched,
        "mismatch_count": len(outcome.mismatches),
        "mismatches": mismatches,
        "pack_precision": [item.model_dump(mode="json") for item in outcome.pack_precision],
    }


def build_repository_validation_record(
    *,
    repository_id: str,
    run_id: str,
    verdict: ValidationVerdict,
    expected: ExpectedResults | None,
    actual: ActualAssessmentResult | None,
    outcome: ComparisonOutcome | None,
    ai_executed: bool = False,
    error_message: str | None = None,
    skip_reason: str | None = None,
    recorded_at: str | None = None,
    record_dir: str | None = None,
) -> RepositoryValidationRecord:
    """Assemble the canonical record payload (does not write)."""

    expected_payload = expected_for_recording(expected) if expected is not None else {}
    actual_payload = actual_for_recording(actual) if actual is not None else {}
    comparison_payload = (
        comparison_for_recording(outcome=outcome, verdict=verdict)
        if outcome is not None
        else {
            "verdict": verdict.value,
            "expectations_evaluated": 0,
            "expectations_matched": 0,
            "mismatch_count": 0,
            "mismatches": [],
            "pack_precision": [],
        }
    )
    pack_precision = outcome.pack_precision if outcome is not None else ()
    mismatches = outcome.mismatches if outcome is not None else ()
    return RepositoryValidationRecord(
        repository_id=repository_id,
        run_id=run_id,
        recorded_at=recorded_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        verdict=verdict,
        schema_version=(
            actual.schema_version
            if actual is not None
            else (expected.schema_version if expected is not None else None)
        ),
        ai_executed=ai_executed,
        expectations_evaluated=(
            outcome.expectations_evaluated if outcome is not None else 0
        ),
        expectations_matched=(
            outcome.expectations_matched if outcome is not None else 0
        ),
        expected=expected_payload,
        actual=actual_payload,
        comparison=comparison_payload,
        pack_precision=pack_precision,
        mismatches=mismatches,
        error_message=error_message,
        skip_reason=skip_reason,
        record_dir=record_dir,
    )


def write_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_repository_validation_record(
    record: RepositoryValidationRecord,
    *,
    records_root: Path = RESULTS_DIR,
    update_latest: bool = True,
) -> Path:
    """Persist expected/actual/comparison/record under runs/ and optional latest/.

    Layout::

        {records_root}/{repository_id}/
          latest/
            expected.json
            actual.json
            comparison.json
            record.json
          runs/{run_id}/
            expected.json
            actual.json
            comparison.json
            record.json
    """

    run_id = record.run_id
    run_dir = run_record_dir(
        record.repository_id,
        run_id,
        records_root=records_root,
    )
    suffix = 1
    while run_dir.exists() and (run_dir / "record.json").is_file():
        suffix += 1
        run_id = f"{record.run_id}_{suffix}"
        run_dir = run_record_dir(
            record.repository_id,
            run_id,
            records_root=records_root,
        )
    if run_id != record.run_id:
        record = record.model_copy(update={"run_id": run_id})

    _write_record_bundle(run_dir, record)

    if update_latest:
        latest_dir = repository_records_root(
            record.repository_id,
            records_root=records_root,
        ) / "latest"
        _write_record_bundle(latest_dir, record)
        pointer = repository_records_root(
            record.repository_id,
            records_root=records_root,
        ) / "latest_run_id.txt"
        pointer.write_text(record.run_id + "\n", encoding="utf-8")

    return run_dir


def load_repository_validation_record(record_dir: Path) -> RepositoryValidationRecord:
    """Load a previously written ``record.json`` for replay/inspection."""

    path = record_dir / "record.json"
    if not path.is_file():
        raise FileNotFoundError(f"validation record missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return RepositoryValidationRecord.model_validate(payload)


def list_run_ids(
    repository_id: str,
    *,
    records_root: Path = RESULTS_DIR,
) -> tuple[str, ...]:
    """Deterministic list of recorded run ids for a repository."""

    runs_dir = repository_records_root(repository_id, records_root=records_root) / "runs"
    if not runs_dir.is_dir():
        return ()
    ids = sorted(
        path.name
        for path in runs_dir.iterdir()
        if path.is_dir() and _RUN_ID_RE.match(path.name) and (path / "record.json").is_file()
    )
    return tuple(ids)


def _safe_record_path(path: str | Path) -> str:
    """Relativize under VALIDATION_ROOT; otherwise basename-only (no home paths)."""

    candidate = Path(path)
    try:
        relative = candidate.resolve().relative_to(VALIDATION_ROOT.resolve())
        return str(relative).replace("\\", "/")
    except ValueError:
        return candidate.name


def _write_record_bundle(directory: Path, record: RepositoryValidationRecord) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    safe_record = record.model_copy(
        update={"record_dir": _safe_record_path(directory)}
    )
    write_json(directory / "expected.json", safe_record.expected)
    write_json(directory / "actual.json", safe_record.actual)
    write_json(directory / "comparison.json", safe_record.comparison)
    write_json(directory / "record.json", safe_record.model_dump(mode="json"))
