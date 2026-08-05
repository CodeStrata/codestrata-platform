"""Deterministic, non-reversible lake object identifier tests (Slice 8.1)."""

from __future__ import annotations

import pytest

from codestrata_platform.community_cloud_api.data_lake.identifiers import (
    LAKE_OBJECT_ID_PREFIX,
    LakeIdentifierError,
    build_lake_object_id,
    build_opaque_object_filename,
)

POLICY_TOKEN = "community-data-lake-policy:1.0"


def test_build_lake_object_id_has_expected_prefix_and_length() -> None:
    identifier = build_lake_object_id(POLICY_TOKEN, "telemetry", "1.0", "event:abcdef123456")
    assert identifier.startswith(LAKE_OBJECT_ID_PREFIX)
    hex_part = identifier[len(LAKE_OBJECT_ID_PREFIX) :]
    assert len(hex_part) == 24
    assert all(ch in "0123456789abcdef" for ch in hex_part)


def test_build_lake_object_id_is_deterministic() -> None:
    first = build_lake_object_id(POLICY_TOKEN, "telemetry", "1.0", "event:same-key")
    second = build_lake_object_id(POLICY_TOKEN, "telemetry", "1.0", "event:same-key")
    assert first == second


@pytest.mark.parametrize(
    "vary",
    ["policy_token", "event_stream", "source_schema_version", "event_key"],
)
def test_build_lake_object_id_changes_with_each_material_component(vary: str) -> None:
    base = dict(
        policy_token=POLICY_TOKEN,
        event_stream="telemetry",
        source_schema_version="1.0",
        event_key="event:abc",
    )
    baseline = build_lake_object_id(**base)
    mutated = dict(base)
    mutated[vary] = mutated[vary] + "-changed"
    assert build_lake_object_id(**mutated) != baseline


def test_build_lake_object_id_rejects_empty_event_key() -> None:
    with pytest.raises(LakeIdentifierError):
        build_lake_object_id(POLICY_TOKEN, "telemetry", "1.0", "")


def test_build_lake_object_id_rejects_whitespace_only_event_key() -> None:
    with pytest.raises(LakeIdentifierError):
        build_lake_object_id(POLICY_TOKEN, "telemetry", "1.0", "   ")


def test_build_lake_object_id_rejects_empty_policy_token() -> None:
    with pytest.raises(LakeIdentifierError):
        build_lake_object_id("", "telemetry", "1.0", "event:abc")


def test_build_lake_object_id_rejects_empty_event_stream() -> None:
    with pytest.raises(LakeIdentifierError):
        build_lake_object_id(POLICY_TOKEN, "", "1.0", "event:abc")


def test_build_lake_object_id_rejects_empty_schema_version() -> None:
    with pytest.raises(LakeIdentifierError):
        build_lake_object_id(POLICY_TOKEN, "telemetry", "", "event:abc")


def test_build_lake_object_id_material_excludes_extraneous_identity() -> None:
    # Same four material fields but supplied via differently-cased/padded
    # whitespace still collapse to the same id (material is 'trimmed').
    padded = build_lake_object_id(
        f"  {POLICY_TOKEN}  ", " telemetry ", " 1.0 ", " event:abc "
    )
    trimmed = build_lake_object_id(POLICY_TOKEN, "telemetry", "1.0", "event:abc")
    assert padded == trimmed


def test_build_opaque_object_filename_format() -> None:
    identifier = build_lake_object_id(POLICY_TOKEN, "telemetry", "1.0", "event:abc")
    filename = build_opaque_object_filename(identifier)
    assert filename.endswith(".json")
    hex_part = filename[: -len(".json")]
    assert len(hex_part) == 24
    assert all(ch in "0123456789abcdef" for ch in hex_part)
    assert identifier == f"{LAKE_OBJECT_ID_PREFIX}{hex_part}"


def test_build_opaque_object_filename_rejects_missing_prefix() -> None:
    with pytest.raises(LakeIdentifierError):
        build_opaque_object_filename("not-a-lake-object-id")


def test_build_opaque_object_filename_rejects_non_hex_body() -> None:
    with pytest.raises(LakeIdentifierError):
        build_opaque_object_filename(f"{LAKE_OBJECT_ID_PREFIX}not-hex-zzz")


def test_build_opaque_object_filename_rejects_empty_body() -> None:
    with pytest.raises(LakeIdentifierError):
        build_opaque_object_filename(LAKE_OBJECT_ID_PREFIX)
