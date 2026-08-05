"""Generic stream-partition projection result and metadata-merge helper (Slice 8.4).

:class:`StorageProjectionResult` is the return shape every stream-specific
partition projector (e.g.
:func:`~.streams.assessment_metadata_partitioning.project_assessment_metadata_storage_object`)
produces: a fully-resolved, already-validated
:class:`~.objects.ImmutableRawStorageObject` plus its bounded
:class:`~.partition_diagnostics.PartitionProjectionDiagnostics`. Nothing in
this module calls a store — persistence stays the caller's responsibility
(see ``store_projected_assessment_metadata`` in the assessment-specific
module for the one-line convenience wrapper used by tests).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.objects import ImmutableRawStorageObject
from codestrata_platform.community_cloud_api.data_lake.partition_diagnostics import (
    PartitionProjectionDiagnostics,
)


@dataclass(frozen=True, slots=True)
class StorageProjectionResult:
    """A resolved, partition-validated storage object plus its diagnostics."""

    storage_object: ImmutableRawStorageObject
    diagnostics: PartitionProjectionDiagnostics

    def to_stable_dict(self) -> dict[str, Any]:
        """Bounded, safe-to-log summary — never the canonical JSON bytes or object key."""

        return {"diagnostics": self.diagnostics.to_stable_dict()}


def merge_extra_s3_metadata(
    storage_object: ImmutableRawStorageObject,
    extra_metadata: Mapping[str, str],
) -> ImmutableRawStorageObject:
    """Return a copy of ``storage_object`` with ``extra_metadata`` merged in.

    A thin, generic wrapper over :func:`dataclasses.replace` so stream-specific
    projectors never need to know that :attr:`ImmutableRawStorageObject.
    extra_s3_metadata` is stored as a sorted tuple of pairs rather than a
    mapping. Re-validates the resulting object and re-derives its S3 metadata
    once (via :meth:`~.objects.ImmutableRawStorageObject.to_s3_metadata`) so
    any not-allowlisted or colliding key fails closed here, at merge time,
    rather than later at write time.

    Returns ``storage_object`` unchanged (no copy) when ``extra_metadata`` is
    empty.
    """

    if not extra_metadata:
        return storage_object
    merged = replace(
        storage_object,
        extra_s3_metadata=tuple(sorted(extra_metadata.items())),
    )
    merged.validate()
    merged.to_s3_metadata()
    return merged
