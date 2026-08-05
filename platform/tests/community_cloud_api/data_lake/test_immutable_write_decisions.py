"""Fail-closed conflict classification and immutable-write build tests (Slice 8.2)."""

from __future__ import annotations

import pytest

from codestrata_platform.community_cloud_api.data_lake.canonical_json import CONTENT_DIGEST_PREFIX
from codestrata_platform.community_cloud_api.data_lake.decisions import (
    classify_existing_object,
    is_valid_content_digest,
)
from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.envelopes import (
    EnvelopeValidationError,
)
from codestrata_platform.community_cloud_api.data_lake.immutable_write import (
    build_immutable_raw_storage_object,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy

from ._envelope_test_helpers import make_envelope

POLICY = CommunityDataLakePolicy.default()
_VALID_DIGEST = CONTENT_DIGEST_PREFIX + ("a" * 64)
_OTHER_DIGEST = CONTENT_DIGEST_PREFIX + ("b" * 64)


def _envelope(**overrides: object) -> object:
    base: dict[str, object] = dict(
        event_stream="cli_event",
        schema_name="community-cli-event",
        schema_version="1.0",
        policy_id="community-cli-event-policy:1.0",
        safe_event_reference="evt-decisionskeyaaaa",
        event_key="event:decisions-key",
        client_type="codestrata_cli",
        payload={"canonical_operation": "assess"},
    )
    base.update(overrides)
    return make_envelope(**base)  # type: ignore[arg-type]


# --- is_valid_content_digest ---


def test_is_valid_content_digest_accepts_well_formed_digest() -> None:
    assert is_valid_content_digest(_VALID_DIGEST) is True


def test_is_valid_content_digest_rejects_missing_prefix() -> None:
    assert is_valid_content_digest("a" * 64) is False


def test_is_valid_content_digest_rejects_uppercase_hex() -> None:
    assert is_valid_content_digest(CONTENT_DIGEST_PREFIX + ("A" * 64)) is False


def test_is_valid_content_digest_rejects_wrong_length() -> None:
    assert is_valid_content_digest(CONTENT_DIGEST_PREFIX + "abc") is False


def test_is_valid_content_digest_rejects_empty_string() -> None:
    assert is_valid_content_digest("") is False


def test_is_valid_content_digest_rejects_non_hex_characters() -> None:
    assert is_valid_content_digest(CONTENT_DIGEST_PREFIX + ("g" * 64)) is False


# --- classify_existing_object (fail-closed) ---


def test_classify_existing_object_none_stored_digest_is_conflict() -> None:
    status = classify_existing_object(requested_digest=_VALID_DIGEST, stored_digest=None)
    assert status is StorageWriteStatus.CONFLICT


def test_classify_existing_object_malformed_stored_digest_is_conflict() -> None:
    status = classify_existing_object(requested_digest=_VALID_DIGEST, stored_digest="garbage")
    assert status is StorageWriteStatus.CONFLICT


def test_classify_existing_object_malformed_requested_digest_is_conflict() -> None:
    status = classify_existing_object(requested_digest="garbage", stored_digest=_VALID_DIGEST)
    assert status is StorageWriteStatus.CONFLICT


def test_classify_existing_object_matching_digests_is_already_exists() -> None:
    status = classify_existing_object(requested_digest=_VALID_DIGEST, stored_digest=_VALID_DIGEST)
    assert status is StorageWriteStatus.ALREADY_EXISTS


def test_classify_existing_object_uppercase_hex_digest_is_malformed_and_fails_closed() -> None:
    # is_valid_content_digest requires LOWERCASE hex; an uppercase digest is
    # malformed and must fail closed to CONFLICT, never ALREADY_EXISTS.
    uppercase_form = _VALID_DIGEST.replace("sha256:", "sha256:").upper().replace("SHA256:", "sha256:")
    assert is_valid_content_digest(uppercase_form) is False
    status = classify_existing_object(requested_digest=_VALID_DIGEST, stored_digest=uppercase_form)
    assert status is StorageWriteStatus.CONFLICT


def test_classify_existing_object_mismatched_digests_is_conflict() -> None:
    status = classify_existing_object(requested_digest=_VALID_DIGEST, stored_digest=_OTHER_DIGEST)
    assert status is StorageWriteStatus.CONFLICT


def test_classify_existing_object_never_returns_stored_or_rejected() -> None:
    # Only ALREADY_EXISTS or CONFLICT may ever be returned by this function.
    for stored in (None, "garbage", _VALID_DIGEST, _OTHER_DIGEST):
        status = classify_existing_object(requested_digest=_VALID_DIGEST, stored_digest=stored)
        assert status in (StorageWriteStatus.ALREADY_EXISTS, StorageWriteStatus.CONFLICT)


# --- build_immutable_raw_storage_object ---


def test_build_immutable_raw_storage_object_succeeds_for_valid_envelope() -> None:
    obj = build_immutable_raw_storage_object(_envelope(), POLICY)
    assert obj.event_stream == "cli_event"
    obj.validate()


def test_build_immutable_raw_storage_object_propagates_envelope_validation_error() -> None:
    with pytest.raises(EnvelopeValidationError):
        build_immutable_raw_storage_object(_envelope(payload={"password": "leak"}), POLICY)


def test_build_immutable_raw_storage_object_is_deterministic() -> None:
    first = build_immutable_raw_storage_object(_envelope(), POLICY)
    second = build_immutable_raw_storage_object(_envelope(), POLICY)
    assert first.object_id == second.object_id
    assert first.object_key == second.object_key
    assert first.content_sha256 == second.content_sha256
    assert first.canonical_json_bytes == second.canonical_json_bytes


def test_build_immutable_raw_storage_object_differs_for_different_payloads() -> None:
    first = build_immutable_raw_storage_object(
        _envelope(payload={"canonical_operation": "assess"}), POLICY
    )
    second = build_immutable_raw_storage_object(
        _envelope(payload={"canonical_operation": "modernize"}), POLICY
    )
    assert first.object_key == second.object_key  # same identity/key
    assert first.content_sha256 != second.content_sha256  # different content
