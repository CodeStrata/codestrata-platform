"""Immutable raw storage object model tests (Slice 8.2)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from codestrata_platform.community_cloud_api.data_lake.canonical_json import CONTENT_DIGEST_PREFIX
from codestrata_platform.community_cloud_api.data_lake.immutable_write import (
    build_immutable_raw_storage_object,
)
from codestrata_platform.community_cloud_api.data_lake.objects import (
    ALLOWED_S3_METADATA_KEYS,
    FORBIDDEN_S3_METADATA_KEYS,
    StorageObjectError,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy

from ._envelope_test_helpers import make_envelope

POLICY = CommunityDataLakePolicy.default()


def _envelope(**overrides: object) -> object:
    base: dict[str, object] = dict(event_key="event:objects-key")
    base.update(overrides)
    return make_envelope(**base)  # type: ignore[arg-type]


def _storage_object():
    return build_immutable_raw_storage_object(_envelope(), POLICY)


def test_build_immutable_raw_storage_object_validates_cleanly() -> None:
    obj = _storage_object()
    obj.validate()  # must not raise


def test_object_key_starts_with_raw_and_ends_with_json() -> None:
    obj = _storage_object()
    assert obj.object_key.startswith("raw/")
    assert obj.object_key.endswith(".json")


def test_opaque_object_id_hex_strips_prefix() -> None:
    obj = _storage_object()
    assert obj.object_id.startswith("lake-object:")
    assert obj.opaque_object_id_hex == obj.object_id.removeprefix("lake-object:")


def test_object_key_filename_matches_object_id() -> None:
    obj = _storage_object()
    assert obj.object_key.endswith(f"/{obj.opaque_object_id_hex}.json")


def test_content_sha256_has_sha256_prefix() -> None:
    obj = _storage_object()
    assert obj.content_sha256.startswith(CONTENT_DIGEST_PREFIX)


def test_to_s3_metadata_only_contains_allowlisted_keys() -> None:
    obj = _storage_object()
    metadata = obj.to_s3_metadata()
    assert set(metadata) <= ALLOWED_S3_METADATA_KEYS
    assert set(metadata) & FORBIDDEN_S3_METADATA_KEYS == set()


def test_to_s3_metadata_object_id_value_is_opaque_hex_without_prefix() -> None:
    obj = _storage_object()
    metadata = obj.to_s3_metadata()
    assert metadata["codestrata-object-id"] == obj.opaque_object_id_hex
    assert "lake-object:" not in metadata["codestrata-object-id"]


def test_to_s3_metadata_never_contains_event_key_or_safe_reference() -> None:
    obj = _storage_object()
    metadata = obj.to_s3_metadata()
    blob = " ".join(metadata.values())
    assert "event:" not in blob
    assert "evt-" not in blob


def test_validate_rejects_wrong_content_type() -> None:
    obj = replace(_storage_object(), content_type="text/plain")
    with pytest.raises(StorageObjectError):
        obj.validate()


def test_validate_rejects_mismatched_content_length() -> None:
    obj = replace(_storage_object(), content_length=999999)
    with pytest.raises(StorageObjectError):
        obj.validate()


def test_validate_rejects_mismatched_digest() -> None:
    bad_digest = CONTENT_DIGEST_PREFIX + ("0" * 64)
    obj = replace(_storage_object(), content_sha256=bad_digest)
    with pytest.raises(StorageObjectError):
        obj.validate()


def test_validate_rejects_malformed_digest_prefix() -> None:
    obj = replace(_storage_object(), content_sha256="not-a-digest")
    with pytest.raises(StorageObjectError):
        obj.validate()


def test_validate_rejects_non_utf8_bytes() -> None:
    obj = replace(_storage_object(), canonical_json_bytes=b"\xff\xfe")
    with pytest.raises(StorageObjectError):
        obj.validate()


def test_validate_rejects_key_without_raw_prefix() -> None:
    original = _storage_object()
    bad_key = original.opaque_object_id_hex + ".json"
    obj = replace(original, object_key=bad_key)
    with pytest.raises(StorageObjectError):
        obj.validate()


def test_validate_rejects_key_with_leading_slash() -> None:
    original = _storage_object()
    obj = replace(original, object_key="/" + original.object_key)
    with pytest.raises(StorageObjectError):
        obj.validate()


def test_validate_rejects_key_with_dot_dot() -> None:
    original = _storage_object()
    obj = replace(original, object_key=f"raw/../{original.opaque_object_id_hex}.json")
    with pytest.raises(StorageObjectError):
        obj.validate()


def test_validate_rejects_key_with_backslash() -> None:
    original = _storage_object()
    obj = replace(original, object_key=original.object_key.replace("/", "\\", 1))
    with pytest.raises(StorageObjectError):
        obj.validate()


def test_validate_rejects_key_not_ending_in_json() -> None:
    original = _storage_object()
    obj = replace(original, object_key=original.object_key.removesuffix(".json"))
    with pytest.raises(StorageObjectError):
        obj.validate()


def test_validate_rejects_key_filename_not_matching_object_id() -> None:
    original = _storage_object()
    obj = replace(original, object_key="raw/stream=telemetry/other-name-not-matching.json")
    with pytest.raises(StorageObjectError):
        obj.validate()


def test_validate_rejects_malformed_object_id_hex() -> None:
    obj = replace(_storage_object(), object_id="lake-object:not-hex-zzzz")
    with pytest.raises(StorageObjectError):
        obj.validate()


def test_validate_rejects_object_id_missing_prefix() -> None:
    obj = replace(_storage_object(), object_id="7f9b7dd557f569c679e19127")
    with pytest.raises(StorageObjectError):
        obj.validate()


def test_validate_rejects_non_object_json_root() -> None:
    obj = replace(_storage_object(), canonical_json_bytes=b"[1,2,3]")
    with pytest.raises(StorageObjectError):
        obj.validate()
