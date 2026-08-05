"""Bounded diagnostics for quarantine projection (Slice 8.9)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ALLOWED_QUARANTINE_PROJECTION_STATUSES: frozenset[str] = frozenset({"projected", "rejected"})

_MAX_SCHEMA_VERSION_LENGTH = 16
_MAX_REFERENCE_LENGTH = 128
_MAX_REASON_LENGTH = 64
_MAX_STAGE_LENGTH = 64


class QuarantineDiagnosticsError(ValueError):
    """Raised when quarantine projection diagnostics fail structural validation."""


def _require_nonblank(value: str, message: str, *, max_length: int = 256) -> str:
    if not isinstance(value, str) or not value.strip():
        raise QuarantineDiagnosticsError(message)
    if len(value) > max_length:
        raise QuarantineDiagnosticsError(f"{message} (exceeds max length {max_length})")
    return value


@dataclass(frozen=True, slots=True)
class QuarantineProjectionDiagnostics:
    """Fixed-shape, privacy-safe diagnostics for one quarantine projection."""

    projection_status: str
    quarantine_reason: str
    validation_stage: str
    quarantine_schema_version: str
    quarantine_policy_version: str
    quarantine_reference: str
    safe_event_reference: str | None = None
    safe_object_reference: str | None = None
    event_stream: str | None = None
    envelope_schema_version: str | None = None
    source_schema_version: str | None = None
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.projection_status not in ALLOWED_QUARANTINE_PROJECTION_STATUSES:
            raise QuarantineDiagnosticsError(
                f"projection_status must be one of {sorted(ALLOWED_QUARANTINE_PROJECTION_STATUSES)}"
            )
        _require_nonblank(
            self.quarantine_reason, "quarantine_reason is required", max_length=_MAX_REASON_LENGTH
        )
        _require_nonblank(
            self.validation_stage, "validation_stage is required", max_length=_MAX_STAGE_LENGTH
        )
        _require_nonblank(
            self.quarantine_schema_version,
            "quarantine_schema_version is required",
            max_length=_MAX_SCHEMA_VERSION_LENGTH,
        )
        _require_nonblank(
            self.quarantine_policy_version,
            "quarantine_policy_version is required",
            max_length=_MAX_SCHEMA_VERSION_LENGTH,
        )
        _require_nonblank(
            self.quarantine_reference,
            "quarantine_reference is required",
            max_length=_MAX_REFERENCE_LENGTH,
        )
        if not self.quarantine_reference.startswith("qz-"):
            raise QuarantineDiagnosticsError("quarantine_reference must start with 'qz-'")
        if self.safe_event_reference is not None:
            _require_nonblank(
                self.safe_event_reference,
                "safe_event_reference, when present, must be non-blank",
                max_length=_MAX_REFERENCE_LENGTH,
            )
            if not self.safe_event_reference.startswith("evt-"):
                raise QuarantineDiagnosticsError(
                    "safe_event_reference must be a safe 'evt-' reference"
                )
        if self.safe_object_reference is not None:
            _require_nonblank(
                self.safe_object_reference,
                "safe_object_reference, when present, must be non-blank",
                max_length=_MAX_REFERENCE_LENGTH,
            )
            if not self.safe_object_reference.startswith("lake-ref:"):
                raise QuarantineDiagnosticsError(
                    "safe_object_reference must be an opaque 'lake-ref:' reference"
                )
        for field_name, value in (
            ("event_stream", self.event_stream),
            ("envelope_schema_version", self.envelope_schema_version),
            ("source_schema_version", self.source_schema_version),
        ):
            if value is not None:
                _require_nonblank(
                    value,
                    f"{field_name}, when present, must be non-blank",
                    max_length=_MAX_SCHEMA_VERSION_LENGTH
                    if field_name != "event_stream"
                    else 64,
                )
        object.__setattr__(self, "limitations", tuple(sorted(set(self.limitations))))

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "limitations": list(self.limitations),
            "projection_status": self.projection_status,
            "quarantine_policy_version": self.quarantine_policy_version,
            "quarantine_reason": self.quarantine_reason,
            "quarantine_reference": self.quarantine_reference,
            "quarantine_schema_version": self.quarantine_schema_version,
            "validation_stage": self.validation_stage,
        }
        if self.envelope_schema_version is not None:
            payload["envelope_schema_version"] = self.envelope_schema_version
        if self.event_stream is not None:
            payload["event_stream"] = self.event_stream
        if self.safe_event_reference is not None:
            payload["safe_event_reference"] = self.safe_event_reference
        if self.safe_object_reference is not None:
            payload["safe_object_reference"] = self.safe_object_reference
        if self.source_schema_version is not None:
            payload["source_schema_version"] = self.source_schema_version
        return {key: payload[key] for key in sorted(payload)}
