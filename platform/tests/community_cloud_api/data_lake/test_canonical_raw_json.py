"""Canonical raw-JSON storage serialization tests (Slice 8.2)."""

from __future__ import annotations

import base64
import hashlib
import json

import pytest

from codestrata_platform.community_cloud_api.data_lake.canonical_json import (
    CONTENT_DIGEST_PREFIX,
    CONTENT_TYPE_APPLICATION_JSON,
    CanonicalJsonError,
    checksum_sha256_b64,
    content_digest_hex,
    digest_matches,
    serialize_canonical_raw_json,
    to_canonical_json_value,
    validate_utf8_json_object_bytes,
)


class _FakeEnvelope:
    def __init__(self, stable: object) -> None:
        self._stable = stable

    def to_stable_dict(self) -> object:
        return self._stable


def test_content_type_is_application_json_constant() -> None:
    assert CONTENT_TYPE_APPLICATION_JSON == "application/json"


def test_serialize_canonical_raw_json_sorts_keys_and_has_no_trailing_newline() -> None:
    envelope = _FakeEnvelope({"b": 2, "a": 1, "nested": {"z": 1, "y": 2}})
    canonical = serialize_canonical_raw_json(envelope)
    assert canonical.data == b'{"a":1,"b":2,"nested":{"y":2,"z":1}}'
    assert not canonical.data.endswith(b"\n")
    assert canonical.content_length == len(canonical.data)


def test_serialize_canonical_raw_json_is_deterministic_across_dict_insertion_order() -> None:
    first = _FakeEnvelope({"a": 1, "b": 2, "c": {"x": 1, "y": 2}})
    second = _FakeEnvelope({"c": {"y": 2, "x": 1}, "b": 2, "a": 1})
    result_a = serialize_canonical_raw_json(first)
    result_b = serialize_canonical_raw_json(second)
    assert result_a.data == result_b.data
    assert result_a.content_sha256 == result_b.content_sha256


def test_serialize_canonical_raw_json_content_sha256_matches_manual_digest() -> None:
    envelope = _FakeEnvelope({"key": "value"})
    canonical = serialize_canonical_raw_json(envelope)
    expected = CONTENT_DIGEST_PREFIX + hashlib.sha256(canonical.data).hexdigest()
    assert canonical.content_sha256 == expected


def test_serialize_canonical_raw_json_preserves_list_order() -> None:
    envelope = _FakeEnvelope({"items": [3, 1, 2]})
    canonical = serialize_canonical_raw_json(envelope)
    assert json.loads(canonical.data) == {"items": [3, 1, 2]}


def test_serialize_canonical_raw_json_rejects_non_dict_root() -> None:
    with pytest.raises(CanonicalJsonError):
        serialize_canonical_raw_json(_FakeEnvelope([1, 2, 3]))


def test_serialize_canonical_raw_json_rejects_nan() -> None:
    with pytest.raises(CanonicalJsonError):
        serialize_canonical_raw_json(_FakeEnvelope({"value": float("nan")}))


def test_serialize_canonical_raw_json_rejects_infinity() -> None:
    with pytest.raises(CanonicalJsonError):
        serialize_canonical_raw_json(_FakeEnvelope({"value": float("inf")}))
    with pytest.raises(CanonicalJsonError):
        serialize_canonical_raw_json(_FakeEnvelope({"value": float("-inf")}))


def test_to_canonical_json_value_rejects_unsupported_type() -> None:
    with pytest.raises(CanonicalJsonError):
        to_canonical_json_value(object())


def test_to_canonical_json_value_uses_to_stable_dict_when_present() -> None:
    nested = _FakeEnvelope({"b": 2, "a": 1})
    assert to_canonical_json_value({"outer": nested}) == {"outer": {"a": 1, "b": 2}}


def test_content_digest_hex_strips_prefix() -> None:
    digest = CONTENT_DIGEST_PREFIX + ("a" * 64)
    assert content_digest_hex(digest) == "a" * 64


def test_content_digest_hex_rejects_missing_prefix() -> None:
    with pytest.raises(CanonicalJsonError):
        content_digest_hex("a" * 64)


def test_content_digest_hex_rejects_wrong_length() -> None:
    with pytest.raises(CanonicalJsonError):
        content_digest_hex(CONTENT_DIGEST_PREFIX + "abc")


def test_digest_matches_true_for_equal_digests_case_insensitive() -> None:
    lower = CONTENT_DIGEST_PREFIX + ("ab" * 32)
    upper = CONTENT_DIGEST_PREFIX + ("AB" * 32)
    assert digest_matches(lower, upper) is True


def test_digest_matches_false_for_different_digests() -> None:
    a = CONTENT_DIGEST_PREFIX + ("a" * 64)
    b = CONTENT_DIGEST_PREFIX + ("b" * 64)
    assert digest_matches(a, b) is False


def test_digest_matches_false_for_malformed_digest() -> None:
    a = CONTENT_DIGEST_PREFIX + ("a" * 64)
    assert digest_matches(a, "not-a-digest") is False
    assert digest_matches("not-a-digest", a) is False


def test_checksum_sha256_b64_matches_manual_base64_of_raw_digest() -> None:
    data = b'{"a":1}'
    expected = base64.b64encode(hashlib.sha256(data).digest()).decode("ascii")
    assert checksum_sha256_b64(data) == expected


def test_validate_utf8_json_object_bytes_round_trips() -> None:
    parsed = validate_utf8_json_object_bytes(b'{"a":1,"b":[1,2,3]}')
    assert parsed == {"a": 1, "b": [1, 2, 3]}


def test_validate_utf8_json_object_bytes_rejects_non_utf8() -> None:
    with pytest.raises(CanonicalJsonError):
        validate_utf8_json_object_bytes(b"\xff\xfe\x00\x01")


def test_validate_utf8_json_object_bytes_rejects_invalid_json() -> None:
    with pytest.raises(CanonicalJsonError):
        validate_utf8_json_object_bytes(b"{not json")


def test_validate_utf8_json_object_bytes_rejects_non_object_root() -> None:
    with pytest.raises(CanonicalJsonError):
        validate_utf8_json_object_bytes(b"[1,2,3]")
    with pytest.raises(CanonicalJsonError):
        validate_utf8_json_object_bytes(b'"just a string"')
