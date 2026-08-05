"""Explicit compatibility matrix: envelope schema 1.0 x five source schemas 1.0 (Slice 8.3).

Slice 8.3 supports exactly one envelope schema version (``1.0``) and exactly
one source schema version per stream (``1.0`` for all five registered
streams). This module makes that matrix an explicit, queryable data
structure rather than an implicit assumption scattered across builders and
validators, so a future schema bump has one obvious place to extend.
"""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.enums import EventStream
from codestrata_platform.community_cloud_api.data_lake.envelope_registry import (
    get_source_contract,
    list_source_contracts,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy

ENVELOPE_SCHEMA_VERSION = CommunityDataLakePolicy.default().envelope_schema_version


def _build_matrix() -> dict[tuple[str, EventStream], str]:
    return {
        (ENVELOPE_SCHEMA_VERSION, descriptor.event_stream): descriptor.schema_version
        for descriptor in list_source_contracts()
    }


COMPATIBILITY_MATRIX: dict[tuple[str, EventStream], str] = _build_matrix()


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
    return expected is not None and expected == source_schema_version


def expected_source_schema_version(event_stream: EventStream | str) -> str:
    """The single supported source schema version for ``event_stream`` at envelope 1.0."""

    return get_source_contract(event_stream).schema_version


def supported_envelope_schema_versions() -> frozenset[str]:
    return frozenset({ENVELOPE_SCHEMA_VERSION})


def supported_event_streams() -> frozenset[EventStream]:
    return frozenset(stream for (_, stream) in COMPATIBILITY_MATRIX)
