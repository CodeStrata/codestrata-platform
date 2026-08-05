"""Stream partition policy contract for the Community Data Lake (Slice 8.4).

A :class:`StreamPartitionPolicy` is the per-stream, versioned declaration of
which envelope/source/assessment schema versions a partition projector may
accept, which Hive path dimensions its object keys must (and may optionally)
carry, and which additional S3 metadata keys/partition field names are
allowlisted or forbidden. It owns none of the generic envelope/object-key
mechanics already implemented by :mod:`.envelopes`, :mod:`.partitions`, and
:mod:`.objects` — it is a bounded, declarative policy record that
:mod:`.stream_partitions` validates object keys and envelopes against.

Slice 8.4 ships exactly one concrete policy
(:func:`~.streams.assessment_metadata_partitioning.default_assessment_metadata_partition_policy`).
Slice 8.5 adds a second, for the ``telemetry`` stream
(:func:`~.streams.telemetry_partitioning.default_telemetry_partition_policy`),
reusing this exact same generic-path-only shape unchanged. Slice 8.6 adds a
third, for the ``cli_event`` stream
(:func:`~.streams.cli_event_partitioning.default_cli_event_partition_policy`),
and introduces one new optional field,
``supported_operation_catalog_versions`` — the CLI operation catalog
version(s) (see
:class:`~codestrata_platform.community_cloud_api.cli_events.catalog.CliOperationCatalog`)
a projector may accept, mirroring the shape of the existing optional
``supported_assessment_schema_versions`` field. It stays empty for streams
with no nested "operation catalog" concept (``telemetry`` and
``assessment_metadata`` leave it at its default). Slice 8.7 reuses that
same operation-catalog field for ``extension_event``. Slice 8.8 adds three
further optional fields for the ``ai_usage`` stream —
``supported_capability_catalog_versions``,
``supported_provider_catalog_versions``, and
``supported_model_catalog_versions`` — kept as *separate* frozensets so
each AI catalog can evolve independently (all currently ``"1.0"``, but
collapsing them into one set would be a compatibility defect). This
module defines the shape only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.enums import EventStream

# Every stream's generic Hive path always carries exactly these five
# dimensions, in this order — see ``platform/docs/community-cloud-api/
# data-lake.md#partition-contract-hive-style``. Slice 8.4 keeps this the
# only supported dimension set for every registered policy (no per-stream
# extra path dimensions).
GENERIC_REQUIRED_PATH_DIMENSIONS: tuple[str, ...] = (
    "stream",
    "schema_version",
    "year",
    "month",
    "day",
)

_MIN_KEY_LENGTH_BOUND = 64
_MAX_KEY_LENGTH_BOUND = 1024


class PartitionPolicyError(ValueError):
    """Raised when a :class:`StreamPartitionPolicy` fails structural validation."""


@dataclass(frozen=True, slots=True)
class StreamPartitionPolicy:
    """Deterministic, versioned partition policy for one event stream.

    ``supported_assessment_schema_versions`` is empty for streams that carry
    no nested "assessment schema" concept (only the assessment metadata
    stream uses it in this slice) — always validated as a bounded,
    normalized frozenset regardless.
    """

    policy_id: str
    policy_version: str
    event_stream: EventStream
    supported_envelope_schema_versions: frozenset[str]
    supported_source_schema_versions: frozenset[str]
    supported_source_policy_ids: frozenset[str]
    supported_assessment_schema_versions: frozenset[str] = frozenset()
    supported_operation_catalog_versions: frozenset[str] = frozenset()
    supported_capability_catalog_versions: frozenset[str] = frozenset()
    supported_provider_catalog_versions: frozenset[str] = frozenset()
    supported_model_catalog_versions: frozenset[str] = frozenset()
    required_path_dimensions: tuple[str, ...] = GENERIC_REQUIRED_PATH_DIMENSIONS
    optional_path_dimensions: tuple[str, ...] = ()
    max_partition_depth: int = 6
    max_key_length: int = 1024
    s3_metadata_allowlist: frozenset[str] = frozenset()
    forbidden_partition_fields: frozenset[str] = frozenset()
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "supported_envelope_schema_versions",
            frozenset(self.supported_envelope_schema_versions),
        )
        object.__setattr__(
            self,
            "supported_source_schema_versions",
            frozenset(self.supported_source_schema_versions),
        )
        object.__setattr__(
            self, "supported_source_policy_ids", frozenset(self.supported_source_policy_ids)
        )
        object.__setattr__(
            self,
            "supported_assessment_schema_versions",
            frozenset(self.supported_assessment_schema_versions),
        )
        object.__setattr__(
            self,
            "supported_operation_catalog_versions",
            frozenset(self.supported_operation_catalog_versions),
        )
        object.__setattr__(
            self,
            "supported_capability_catalog_versions",
            frozenset(self.supported_capability_catalog_versions),
        )
        object.__setattr__(
            self,
            "supported_provider_catalog_versions",
            frozenset(self.supported_provider_catalog_versions),
        )
        object.__setattr__(
            self,
            "supported_model_catalog_versions",
            frozenset(self.supported_model_catalog_versions),
        )
        object.__setattr__(
            self, "required_path_dimensions", tuple(self.required_path_dimensions)
        )
        object.__setattr__(
            self, "optional_path_dimensions", tuple(self.optional_path_dimensions)
        )
        object.__setattr__(self, "s3_metadata_allowlist", frozenset(self.s3_metadata_allowlist))
        object.__setattr__(
            self, "forbidden_partition_fields", frozenset(self.forbidden_partition_fields)
        )
        object.__setattr__(self, "limitations", tuple(sorted(set(self.limitations))))
        self.validate()

    @property
    def policy_token(self) -> str:
        return f"{self.policy_id}:{self.policy_version}"

    def validate(self) -> None:
        """Raise :class:`PartitionPolicyError` when any structural invariant is violated."""

        if not self.policy_id or not self.policy_id.strip():
            raise PartitionPolicyError("policy_id is required")
        if not self.policy_version or not self.policy_version.strip():
            raise PartitionPolicyError("policy_version is required")
        if not isinstance(self.event_stream, EventStream):
            raise PartitionPolicyError("event_stream must be an EventStream member")
        if not self.supported_envelope_schema_versions:
            raise PartitionPolicyError("supported_envelope_schema_versions must not be empty")
        if not self.supported_source_schema_versions:
            raise PartitionPolicyError("supported_source_schema_versions must not be empty")
        if not self.supported_source_policy_ids:
            raise PartitionPolicyError("supported_source_policy_ids must not be empty")
        for urn in self.supported_source_policy_ids:
            if not urn or ":" not in urn:
                raise PartitionPolicyError(
                    "supported_source_policy_ids entries must be full URNs (id:version)"
                )
        if not self.required_path_dimensions:
            raise PartitionPolicyError("required_path_dimensions must not be empty")
        if tuple(self.required_path_dimensions) != GENERIC_REQUIRED_PATH_DIMENSIONS:
            raise PartitionPolicyError(
                "required_path_dimensions must be exactly the generic "
                f"{GENERIC_REQUIRED_PATH_DIMENSIONS!r} dimension set in Slice 8.4"
            )
        overlap = set(self.required_path_dimensions) & set(self.optional_path_dimensions)
        if overlap:
            raise PartitionPolicyError(
                f"required and optional path dimensions must not overlap: {sorted(overlap)}"
            )
        if self.optional_path_dimensions:
            raise PartitionPolicyError(
                "optional_path_dimensions must be empty in Slice 8.4 (generic path only)"
            )
        if self.max_partition_depth < len(self.required_path_dimensions):
            raise PartitionPolicyError(
                "max_partition_depth must be at least len(required_path_dimensions)"
            )
        if not (_MIN_KEY_LENGTH_BOUND <= self.max_key_length <= _MAX_KEY_LENGTH_BOUND):
            raise PartitionPolicyError(
                f"max_key_length out of bounds [{_MIN_KEY_LENGTH_BOUND}, {_MAX_KEY_LENGTH_BOUND}]"
            )
        if not self.s3_metadata_allowlist:
            raise PartitionPolicyError("s3_metadata_allowlist must not be empty")
        forbidden_overlap = set(self.required_path_dimensions) & set(
            self.forbidden_partition_fields
        )
        if forbidden_overlap:
            raise PartitionPolicyError(
                "forbidden_partition_fields must not include a required path dimension: "
                f"{sorted(forbidden_overlap)}"
            )

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "event_stream": self.event_stream.value,
            "forbidden_partition_fields": sorted(self.forbidden_partition_fields),
            "limitations": list(self.limitations),
            "max_key_length": self.max_key_length,
            "max_partition_depth": self.max_partition_depth,
            "optional_path_dimensions": list(self.optional_path_dimensions),
            "policy_id": self.policy_id,
            "policy_token": self.policy_token,
            "policy_version": self.policy_version,
            "required_path_dimensions": list(self.required_path_dimensions),
            "s3_metadata_allowlist": sorted(self.s3_metadata_allowlist),
            "supported_assessment_schema_versions": sorted(
                self.supported_assessment_schema_versions
            ),
            "supported_capability_catalog_versions": sorted(
                self.supported_capability_catalog_versions
            ),
            "supported_envelope_schema_versions": sorted(
                self.supported_envelope_schema_versions
            ),
            "supported_model_catalog_versions": sorted(
                self.supported_model_catalog_versions
            ),
            "supported_operation_catalog_versions": sorted(
                self.supported_operation_catalog_versions
            ),
            "supported_provider_catalog_versions": sorted(
                self.supported_provider_catalog_versions
            ),
            "supported_source_policy_ids": sorted(self.supported_source_policy_ids),
            "supported_source_schema_versions": sorted(
                self.supported_source_schema_versions
            ),
        }
