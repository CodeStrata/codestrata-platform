"""Envelope schema compatibility matrix tests (Slice 8.3 / 20.7)."""

from __future__ import annotations

import pytest

from codestrata_platform.community_cloud_api.data_lake.enums import EventStream
from codestrata_platform.community_cloud_api.data_lake.schema_compatibility import (
    COMPATIBILITY_MATRIX,
    ENVELOPE_SCHEMA_VERSION,
    expected_source_schema_version,
    is_compatible,
    supported_envelope_schema_versions,
    supported_event_streams,
    supported_source_schema_versions,
)


def test_envelope_schema_version_is_1_0() -> None:
    assert ENVELOPE_SCHEMA_VERSION == "1.0"


def test_matrix_has_exactly_five_entries() -> None:
    assert len(COMPATIBILITY_MATRIX) == 5


@pytest.mark.parametrize("stream", list(EventStream))
def test_matrix_covers_every_stream_at_envelope_1_0(stream: EventStream) -> None:
    versions = COMPATIBILITY_MATRIX[("1.0", stream)]
    assert "1.0" in versions
    if stream is EventStream.ASSESSMENT_METADATA:
        assert versions == frozenset({"1.0", "1.1"})
    else:
        assert versions == frozenset({"1.0"})


@pytest.mark.parametrize("stream", list(EventStream))
def test_is_compatible_true_for_registered_envelope_stream_and_source_versions(
    stream: EventStream,
) -> None:
    assert is_compatible("1.0", stream, "1.0") is True


def test_assessment_metadata_1_1_is_compatible() -> None:
    assert is_compatible("1.0", EventStream.ASSESSMENT_METADATA, "1.1") is True
    assert supported_source_schema_versions(EventStream.ASSESSMENT_METADATA) == frozenset(
        {"1.0", "1.1"}
    )


def test_is_compatible_false_for_unsupported_envelope_schema_version() -> None:
    assert is_compatible("9.9", EventStream.TELEMETRY, "1.0") is False


def test_is_compatible_false_for_unsupported_source_schema_version() -> None:
    assert is_compatible("1.0", EventStream.TELEMETRY, "9.9") is False
    assert is_compatible("1.0", EventStream.ASSESSMENT_METADATA, "9.9") is False


def test_is_compatible_false_for_unknown_stream_string() -> None:
    assert is_compatible("1.0", "not_a_real_stream", "1.0") is False


def test_is_compatible_accepts_string_stream_value() -> None:
    assert is_compatible("1.0", "telemetry", "1.0") is True


@pytest.mark.parametrize("stream", list(EventStream))
def test_expected_source_schema_version_returns_1_0_baseline_for_every_stream(
    stream: EventStream,
) -> None:
    assert expected_source_schema_version(stream) == "1.0"


def test_supported_envelope_schema_versions_is_a_singleton_of_1_0() -> None:
    assert supported_envelope_schema_versions() == frozenset({"1.0"})


def test_supported_event_streams_covers_every_enum_member() -> None:
    assert supported_event_streams() == frozenset(EventStream)
