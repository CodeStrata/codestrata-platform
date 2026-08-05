"""Slice 8.3 structural privacy scan tests — forbidden field NAMES (Slice 8.3).

Complements ``test_privacy.py`` (Slice 8.1 coarse blob-substring scan).
These tests target :data:`FORBIDDEN_ENVELOPE_KEY_NAMES` and
:func:`validate_envelope_privacy`'s structural key-path pass, which matches
exact (case-insensitive) key names at any nesting depth rather than
substrings — so legitimate enum values that happen to contain a forbidden
token never false-positive.
"""

from __future__ import annotations

import pytest

from codestrata_platform.community_cloud_api.data_lake.envelopes import (
    FORBIDDEN_ENVELOPE_KEY_NAMES,
    EnvelopeValidationError,
    validate_envelope_privacy,
)

from ._envelope_test_helpers import make_envelope


@pytest.mark.parametrize("forbidden_name", sorted(FORBIDDEN_ENVELOPE_KEY_NAMES))
def test_every_forbidden_key_name_is_rejected_as_a_top_level_payload_key(
    forbidden_name: str,
) -> None:
    # build_envelope() already privacy-validates at construction time, so the
    # rejection happens on this call, not on a later explicit re-validation.
    with pytest.raises(EnvelopeValidationError):
        make_envelope(payload={forbidden_name: "some-value"})


@pytest.mark.parametrize("forbidden_name", sorted(FORBIDDEN_ENVELOPE_KEY_NAMES))
def test_every_forbidden_key_name_is_rejected_when_nested_deep_in_payload(
    forbidden_name: str,
) -> None:
    with pytest.raises(EnvelopeValidationError):
        make_envelope(payload={"outer": {"inner": {forbidden_name: "value"}}})


@pytest.mark.parametrize("forbidden_name", sorted(FORBIDDEN_ENVELOPE_KEY_NAMES))
def test_every_forbidden_key_name_is_rejected_inside_a_list_of_objects(
    forbidden_name: str,
) -> None:
    with pytest.raises(EnvelopeValidationError):
        make_envelope(payload={"items": [{"a": 1}, {forbidden_name: "value"}]})


def test_forbidden_key_name_matching_is_case_insensitive() -> None:
    with pytest.raises(EnvelopeValidationError):
        make_envelope(payload={"Authorization": "value"})


def test_forbidden_key_name_matching_is_exact_not_substring() -> None:
    # "response" is forbidden, but "response_time_bucket" is a distinct key
    # name and must not be false-positived by a substring scan.
    envelope = make_envelope(payload={"response_time_bucket": "1s_to_5s"})
    validate_envelope_privacy(envelope)  # must not raise


def test_legitimate_enum_value_containing_forbidden_substring_is_not_rejected() -> None:
    # "authentication_failed" contains "auth" but is a legitimate outcome
    # enum value, not a key name — the structural scan only inspects keys.
    envelope = make_envelope(payload={"outcome": "authentication_failed"})
    validate_envelope_privacy(envelope)  # must not raise


def test_event_id_is_allowed_inside_payload() -> None:
    envelope = make_envelope(payload={"event_id": "evt-test-0001"})
    validate_envelope_privacy(envelope)  # must not raise


def test_installation_id_is_allowed_inside_payload() -> None:
    envelope = make_envelope(payload={"installation_id": "install-abcdef12"})
    validate_envelope_privacy(envelope)  # must not raise


def test_clean_default_envelope_passes_privacy_validation() -> None:
    envelope = make_envelope()
    validate_envelope_privacy(envelope)  # must not raise


def test_forbidden_key_name_in_top_level_envelope_dict_would_be_impossible_by_construction() -> None:
    # The top-level envelope shape is fixed (acceptance/client/envelope_schema_version/
    # event_stream/identity/payload/source_contract) — none of those names are
    # forbidden, so only payload-nested keys can trigger this scan in practice.
    envelope = make_envelope()
    stable = envelope.to_stable_dict()
    assert not (set(stable) & FORBIDDEN_ENVELOPE_KEY_NAMES)
