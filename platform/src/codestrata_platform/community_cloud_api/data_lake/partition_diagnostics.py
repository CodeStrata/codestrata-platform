"""Bounded, privacy-safe diagnostics for one stream partition projection (Slice 8.4).

:class:`PartitionProjectionDiagnostics` is the *only* diagnostic surface a
partition projector (e.g.
:mod:`.streams.assessment_metadata_partitioning`,
:mod:`.streams.telemetry_partitioning`) may return alongside a
projected storage object. Its field set is a fixed allowlist — event/source
schema versions, the partition policy version, a validity flag, a bounded
status string, and the two existing opaque reference formats
(``evt-…``/``lake-ref:…``) already used elsewhere in this package. It never
carries ``event_id``, ``installation_id``, the object key, bucket name,
content digest, payload fragments, counts, executed heads, or language —
those remain private payload/storage-object concerns, not diagnostics.

Slice 8.5 adds one more optional field, ``client_type`` — the telemetry
stream's bounded client-type classification (mirroring the shape of the
existing optional ``assessment_schema_version`` field). Only the telemetry
projector ever sets it; the assessment metadata projector continues to
leave it ``None``.

Slice 8.6 adds one more optional field, ``operation_catalog_version`` — the
CLI operation catalog version (e.g. ``"1.0"``) the ``cli_event`` stream's
projector validated the submitted ``operation`` against (mirroring the
shape of ``assessment_schema_version``/``client_type``). Only the CLI event
projector ever sets it; ``client_type`` is left ``None`` for that stream's
diagnostics (the CLI client is always ``codestrata_cli`` — redundant to
surface here). Slice 8.7 reuses ``operation_catalog_version`` for
``extension_event`` (and *also* sets ``client_type``).

Slice 8.8 adds three more optional fields for the ``ai_usage`` stream —
``capability_catalog_version``, ``provider_catalog_version``, and
``model_catalog_version`` — kept separate so each AI catalog can evolve
independently. Only the AI usage projector sets them; other streams leave
them ``None``. The AI usage projector also sets ``client_type`` (Option B
metadata) and leaves ``operation_catalog_version`` ``None``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Bounded, stable projection outcomes. Only "projected" is produced by any
# Slice 8.4 call site (every rejection path raises ``PartitionProjectionError``
# instead of returning diagnostics) — "rejected" is reserved for a future
# diagnostics-only (non-raising) call site and is accepted here so this
# dataclass does not need to change shape when one is added.
ALLOWED_PROJECTION_STATUSES: frozenset[str] = frozenset({"projected", "rejected"})

_MAX_SCHEMA_VERSION_LENGTH = 16
_MAX_REFERENCE_LENGTH = 128
_MAX_CLIENT_TYPE_LENGTH = 64
_MAX_OPERATION_CATALOG_VERSION_LENGTH = 16


class PartitionDiagnosticsError(ValueError):
    """Raised when :class:`PartitionProjectionDiagnostics` fails structural validation."""


def _require_nonblank(value: str, message: str, *, max_length: int = 256) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PartitionDiagnosticsError(message)
    if len(value) > max_length:
        raise PartitionDiagnosticsError(f"{message} (exceeds max length {max_length})")
    return value


@dataclass(frozen=True, slots=True)
class PartitionProjectionDiagnostics:
    """Fixed-shape, privacy-safe diagnostics for one partition projection attempt."""

    event_stream: str
    envelope_schema_version: str
    source_schema_version: str
    partition_policy_version: str
    partition_valid: bool
    projection_status: str
    safe_event_reference: str
    safe_object_reference: str
    assessment_schema_version: str | None = None
    client_type: str | None = None
    operation_catalog_version: str | None = None
    capability_catalog_version: str | None = None
    provider_catalog_version: str | None = None
    model_catalog_version: str | None = None
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_nonblank(self.event_stream, "event_stream is required", max_length=64)
        _require_nonblank(
            self.envelope_schema_version,
            "envelope_schema_version is required",
            max_length=_MAX_SCHEMA_VERSION_LENGTH,
        )
        _require_nonblank(
            self.source_schema_version,
            "source_schema_version is required",
            max_length=_MAX_SCHEMA_VERSION_LENGTH,
        )
        _require_nonblank(
            self.partition_policy_version,
            "partition_policy_version is required",
            max_length=_MAX_SCHEMA_VERSION_LENGTH,
        )
        if not isinstance(self.partition_valid, bool):
            raise PartitionDiagnosticsError("partition_valid must be a bool")
        if self.projection_status not in ALLOWED_PROJECTION_STATUSES:
            raise PartitionDiagnosticsError(
                f"projection_status must be one of {sorted(ALLOWED_PROJECTION_STATUSES)}"
            )
        _require_nonblank(
            self.safe_event_reference,
            "safe_event_reference is required",
            max_length=_MAX_REFERENCE_LENGTH,
        )
        if not self.safe_event_reference.startswith("evt-"):
            raise PartitionDiagnosticsError("safe_event_reference must be a safe 'evt-' reference")
        _require_nonblank(
            self.safe_object_reference,
            "safe_object_reference is required",
            max_length=_MAX_REFERENCE_LENGTH,
        )
        if not self.safe_object_reference.startswith("lake-ref:"):
            raise PartitionDiagnosticsError(
                "safe_object_reference must be an opaque 'lake-ref:' reference"
            )
        if self.assessment_schema_version is not None:
            if (
                not isinstance(self.assessment_schema_version, str)
                or not self.assessment_schema_version.strip()
            ):
                raise PartitionDiagnosticsError(
                    "assessment_schema_version, when present, must be a non-blank string"
                )
            if len(self.assessment_schema_version) > _MAX_SCHEMA_VERSION_LENGTH:
                raise PartitionDiagnosticsError("assessment_schema_version exceeds max length")
        if self.client_type is not None:
            if not isinstance(self.client_type, str) or not self.client_type.strip():
                raise PartitionDiagnosticsError(
                    "client_type, when present, must be a non-blank string"
                )
            if len(self.client_type) > _MAX_CLIENT_TYPE_LENGTH:
                raise PartitionDiagnosticsError("client_type exceeds max length")
        if self.operation_catalog_version is not None:
            if (
                not isinstance(self.operation_catalog_version, str)
                or not self.operation_catalog_version.strip()
            ):
                raise PartitionDiagnosticsError(
                    "operation_catalog_version, when present, must be a non-blank string"
                )
            if len(self.operation_catalog_version) > _MAX_OPERATION_CATALOG_VERSION_LENGTH:
                raise PartitionDiagnosticsError("operation_catalog_version exceeds max length")
        for field_name, value in (
            ("capability_catalog_version", self.capability_catalog_version),
            ("provider_catalog_version", self.provider_catalog_version),
            ("model_catalog_version", self.model_catalog_version),
        ):
            if value is not None:
                if not isinstance(value, str) or not value.strip():
                    raise PartitionDiagnosticsError(
                        f"{field_name}, when present, must be a non-blank string"
                    )
                if len(value) > _MAX_OPERATION_CATALOG_VERSION_LENGTH:
                    raise PartitionDiagnosticsError(f"{field_name} exceeds max length")
        object.__setattr__(self, "limitations", tuple(sorted(set(self.limitations))))

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "envelope_schema_version": self.envelope_schema_version,
            "event_stream": self.event_stream,
            "limitations": list(self.limitations),
            "partition_policy_version": self.partition_policy_version,
            "partition_valid": self.partition_valid,
            "projection_status": self.projection_status,
            "safe_event_reference": self.safe_event_reference,
            "safe_object_reference": self.safe_object_reference,
            "source_schema_version": self.source_schema_version,
        }
        if self.assessment_schema_version is not None:
            payload["assessment_schema_version"] = self.assessment_schema_version
        if self.capability_catalog_version is not None:
            payload["capability_catalog_version"] = self.capability_catalog_version
        if self.client_type is not None:
            payload["client_type"] = self.client_type
        if self.model_catalog_version is not None:
            payload["model_catalog_version"] = self.model_catalog_version
        if self.operation_catalog_version is not None:
            payload["operation_catalog_version"] = self.operation_catalog_version
        if self.provider_catalog_version is not None:
            payload["provider_catalog_version"] = self.provider_catalog_version
        return {key: payload[key] for key in sorted(payload)}
