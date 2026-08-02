"""Committed false-negative adjudications (Slice 5.10).

Adjudications live under ``engine/validation/adjudications/false_negatives/``
and are never overwritten by generated validation records.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from codestrata.domain.graph.validation import as_tuple, require_nonblank
from codestrata.domain.quality_metrics.common import dedupe_limitations
from codestrata.domain.quality_metrics.false_negatives import (
    FalseNegativeClassification,
    FalseNegativeRecord,
    FalseNegativeResolution,
    FalseNegativeRootCause,
    FalseNegativeStatus,
)
from validation.paths import VALIDATION_ROOT

ADJUDICATIONS_DIR = VALIDATION_ROOT / "adjudications" / "false_negatives"


class FalseNegativeAdjudication(BaseModel):
    """Committed review decision for one false_negative_id."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    false_negative_id: str
    classification: FalseNegativeClassification
    status: FalseNegativeStatus
    root_cause: FalseNegativeRootCause | None = None
    resolution: FalseNegativeResolution | None = None
    rationale: str | None = None
    reviewer_note: str | None = None
    source_evidence_note: str | None = None
    supported_scope_note: str | None = None
    regression_test_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    @field_validator("false_negative_id", mode="before")
    @classmethod
    def normalize_id(cls, value: object) -> str:
        text = require_nonblank(str(value), label="false_negative_id")
        if not text.startswith("fn:"):
            raise ValueError("false_negative_id must use fn: prefix")
        return text

    @field_validator("regression_test_refs", mode="before")
    @classmethod
    def normalize_refs(cls, value: object) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    require_nonblank(str(item), label="regression_test_ref")
                    for item in as_tuple(value)
                }
            )
        )

    @field_validator("limitations", mode="before")
    @classmethod
    def normalize_limitations(cls, value: object) -> tuple[str, ...]:
        return dedupe_limitations(value, label="adjudication limitation")

    @field_validator(
        "rationale",
        "reviewer_note",
        "source_evidence_note",
        "supported_scope_note",
        mode="before",
    )
    @classmethod
    def optional_text(cls, value: object) -> str | None:
        if value is None:
            return None
        text = " ".join(str(value).split())
        return text or None

    @model_validator(mode="after")
    def validate_adjudication(self) -> FalseNegativeAdjudication:
        if (
            self.classification is FalseNegativeClassification.CONFIRMED
            and self.status is FalseNegativeStatus.FIXED
        ):
            if self.root_cause is None or self.resolution is None:
                raise ValueError(
                    "confirmed→fixed adjudication requires root_cause and resolution"
                )
            if (
                self.resolution is FalseNegativeResolution.PRODUCT_FIX
                and not self.regression_test_refs
            ):
                raise ValueError("product_fix adjudication requires regression_test_refs")
        if self.classification is FalseNegativeClassification.CONFIRMED and (
            self.root_cause
            in {
                FalseNegativeRootCause.EXPECTATION_ERROR,
                FalseNegativeRootCause.UNSUPPORTED_CAPABILITY,
            }
        ):
            raise ValueError(
                "confirmed adjudication cannot use expectation_error or "
                "unsupported_capability root cause"
            )
        return self


def adjudication_path(
    false_negative_id: str,
    *,
    adjudications_dir: Path = ADJUDICATIONS_DIR,
) -> Path:
    safe = false_negative_id.replace(":", "_")
    return adjudications_dir / f"{safe}.json"


def load_adjudication(
    false_negative_id: str,
    *,
    adjudications_dir: Path = ADJUDICATIONS_DIR,
) -> FalseNegativeAdjudication | None:
    path = adjudication_path(false_negative_id, adjudications_dir=adjudications_dir)
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return FalseNegativeAdjudication.model_validate(payload)


def load_adjudications(
    *,
    adjudications_dir: Path = ADJUDICATIONS_DIR,
) -> dict[str, FalseNegativeAdjudication]:
    if not adjudications_dir.is_dir():
        return {}
    loaded: dict[str, FalseNegativeAdjudication] = {}
    for path in sorted(adjudications_dir.glob("fn_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        item = FalseNegativeAdjudication.model_validate(payload)
        loaded[item.false_negative_id] = item
    return loaded


def apply_adjudication(
    record: FalseNegativeRecord,
    adjudication: FalseNegativeAdjudication | None,
    *,
    resolved_run_id: str | None = None,
) -> FalseNegativeRecord:
    """Overlay committed adjudication onto a generated FN record."""

    if adjudication is None:
        return record
    if adjudication.false_negative_id != record.false_negative_id:
        raise ValueError("adjudication false_negative_id mismatch")
    updates: dict[str, Any] = {
        "classification": adjudication.classification,
        "status": adjudication.status,
        "root_cause": adjudication.root_cause or record.root_cause,
        "resolution": adjudication.resolution or record.resolution,
        "rationale": adjudication.rationale or record.rationale,
        "regression_test_refs": tuple(
            sorted(set(record.regression_test_refs) | set(adjudication.regression_test_refs))
        ),
        "limitations": dedupe_limitations(
            (
                *record.limitations,
                *adjudication.limitations,
                "adjudication applied from committed validation/adjudications/false_negatives",
            ),
            label="false negative limitation",
        ),
    }
    if adjudication.reviewer_note:
        updates["limitations"] = dedupe_limitations(
            (*updates["limitations"], f"reviewer_note: {adjudication.reviewer_note}"),
            label="false negative limitation",
        )
    if adjudication.supported_scope_note:
        updates["limitations"] = dedupe_limitations(
            (
                *updates["limitations"],
                f"supported_scope_note: {adjudication.supported_scope_note}",
            ),
            label="false negative limitation",
        )
    if adjudication.status is FalseNegativeStatus.FIXED:
        updates["resolved_run_id"] = (
            resolved_run_id or record.resolved_run_id or record.last_seen_run_id
        )
    return record.model_copy(update=updates)
