"""Explicit compatibility matrix: envelope schema 1.0 × source schemas (Slice 8.3 / 20.7).

Slice 8.3 supported exactly one envelope schema version (``1.0``) and one
source schema version per stream (``1.0``). Slice 20.7 extends
``assessment_metadata`` to also accept additive source schema ``1.1`` while
keeping envelope ``1.0`` and other streams at source ``1.0``.
"""

from __future__ import annotations

from codestrata_platform.community_cloud_api.assessment_metadata.policy import (
    COMMUNITY_ASSESSMENT_METADATA_SUPPORTED_SCHEMA_VERSIONS,
)
from codestrata_platform.community_cloud_api.data_lake.enums import EventStream
from codestrata_platform.community_cloud_api.data_lake.envelope_registry import (
    get_source_contract,
    list_source_contracts,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy

ENVELOPE_SCHEMA_VERSION = CommunityDataLakePolicy.default().envelope_schema_version


def _build_matrix() -> dict[tuple[str, EventStream], frozenset[str]]:
    matrix: dict[tuple[str, EventStream], frozenset[str]] = {}
    for descriptor in list_source_contracts():
        supported = descriptor.supported_schema_versions or frozenset(
            {descriptor.schema_version}
        )
        matrix[(ENVELOPE_SCHEMA_VERSION, descriptor.event_stream)] = frozenset(supported)
    return matrix


COMPATIBILITY_MATRIX: dict[tuple[str, EventStream], frozenset[str]] = _build_matrix()


def is_compatible(
    envelope_schema_version: str,
    event_stream: EventStream | str,
    source_schema_version: str,
) -> bool:
    """Return whether the given (envelope, stream, source-schema) triple is supported."""

    try:
        stream = event_stream if isinstance(event_stream, EventStream) else EventStream(event_stream)
    except ValueError:
        return False
    expected = COMPATIBILITY_MATRIX.get((envelope_schema_version, stream))
    return expected is not None and source_schema_version in expected


def expected_source_schema_version(event_stream: EventStream | str) -> str:
    """Baseline/default source schema version for ``event_stream`` at envelope 1.0."""

    return get_source_contract(event_stream).schema_version


def supported_source_schema_versions(event_stream: EventStream | str) -> frozenset[str]:
    """All accepted source schema versions for ``event_stream`` at envelope 1.0."""

    try:
        stream = event_stream if isinstance(event_stream, EventStream) else EventStream(event_stream)
    except ValueError as exc:
        raise KeyError(event_stream) from exc
    versions = COMPATIBILITY_MATRIX.get((ENVELOPE_SCHEMA_VERSION, stream))
    if versions is None:
        raise KeyError(event_stream)
    return versions


def supported_envelope_schema_versions() -> frozenset[str]:
    return frozenset({ENVELOPE_SCHEMA_VERSION})


def supported_event_streams() -> frozenset[EventStream]:
    return frozenset(stream for (_, stream) in COMPATIBILITY_MATRIX)


# Re-export for callers that need the assessment_metadata dual-version set.
ASSESSMENT_METADATA_SUPPORTED_SOURCE_SCHEMAS = (
    COMMUNITY_ASSESSMENT_METADATA_SUPPORTED_SCHEMA_VERSIONS
)
