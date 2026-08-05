"""Privacy boundary tests for the Community Data Lake domain (Slice 8.1)."""

from __future__ import annotations

import json

import pytest

from codestrata_platform.community_cloud_api.data_lake.diagnostics import (
    safe_storage_diagnostic,
    sanitize_exception_message,
)
from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.envelopes import (
    EnvelopeValidationError,
)
from codestrata_platform.community_cloud_api.data_lake.identifiers import build_lake_object_id
from codestrata_platform.community_cloud_api.data_lake.partitions import (
    build_accepted_object_key,
    build_quarantine_object_key,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.data_lake.ports import InMemoryCommunityDataLakeStore

from ._envelope_test_helpers import make_envelope

POLICY_TOKEN = CommunityDataLakePolicy.default().policy_token


def _envelope(**overrides: object) -> object:
    base: dict[str, object] = dict(
        event_stream="extension_event",
        schema_name="community-extension-event",
        schema_version="1.0",
        policy_id="community-extension-event-policy:1.0",
        safe_event_reference="evt-ffffffffffff",
        event_key="event:privacy-key",
        client_type="vscode_extension",
        payload={"lifecycle": "completed"},
    )
    base.update(overrides)
    return make_envelope(**base)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "raw_field,raw_value",
    [
        ("authorization", "Bearer abc123"),
        ("cookie", "session=abc"),
        ("ip_address", "10.0.0.1"),
        ("client_ip", "10.0.0.1"),
        ("request_id", "req-abc-123"),
        ("password", "hunter2"),
        ("secret", "s3cr3t"),
        ("bearer", "token"),
        ("access_key", "AKIA0000000000000000"),
        ("private_key", "-----BEGIN PRIVATE KEY-----"),
        ("aws_secret", "value"),
    ],
)
def test_raw_identity_fields_are_rejected_anywhere_in_payload(
    raw_field: str, raw_value: str
) -> None:
    with pytest.raises(EnvelopeValidationError):
        _envelope(payload={raw_field: raw_value})


def test_client_credential_prefix_is_rejected_in_payload() -> None:
    with pytest.raises(EnvelopeValidationError):
        _envelope(payload={"token": "cscc_v1_abcdef"})


def test_object_key_never_contains_event_key_or_safe_reference() -> None:
    envelope = _envelope()
    lake_object_id = build_lake_object_id(
        POLICY_TOKEN, envelope.event_stream, envelope.source_schema_version, envelope.event_key
    )
    key = build_accepted_object_key(envelope, lake_object_id)
    assert envelope.event_key not in key
    assert envelope.safe_event_reference not in key
    assert "event:" not in key
    assert "evt-" not in key


def test_quarantine_object_key_never_contains_safe_event_reference() -> None:
    safe_ref = "evt-gggggggggggg"
    lake_object_id = build_lake_object_id(POLICY_TOKEN, "cli_event", "1.0", "event:quarantine-me")
    key = build_quarantine_object_key("unsafe_payload", "2026", "08", "03", lake_object_id)
    assert safe_ref not in key
    assert "evt-" not in key


def test_safe_storage_diagnostic_never_echoes_payload() -> None:
    diagnostic = safe_storage_diagnostic(StorageWriteStatus.REJECTED, reason_code="unsafe_payload")
    blob = json.dumps(diagnostic)
    assert "password" not in blob
    assert "payload" not in diagnostic
    assert set(diagnostic) <= {"status", "reason_code"}


def test_safe_storage_diagnostic_omits_reason_code_when_absent() -> None:
    diagnostic = safe_storage_diagnostic(StorageWriteStatus.STORED)
    assert diagnostic == {"status": "stored"}


def test_sanitize_exception_message_never_includes_exception_text() -> None:
    exc = ValueError("secret-token=abc123 /Users/alice/leak.txt")
    sanitized = sanitize_exception_message(exc)
    assert sanitized == "ValueError"
    assert "secret-token" not in sanitized
    assert "/Users/" not in sanitized


def test_sanitize_exception_message_is_bounded_length() -> None:
    class ALongExceptionTypeNameThatExceedsTheBoundedLimitForSanitizedDiagnostics(Exception):
        pass

    exc = ALongExceptionTypeNameThatExceedsTheBoundedLimitForSanitizedDiagnostics("x")
    sanitized = sanitize_exception_message(exc)
    assert len(sanitized) <= 64


def test_store_rejection_detail_never_leaks_payload_via_sanitized_exception() -> None:
    store = InMemoryCommunityDataLakeStore()
    from codestrata_platform.community_cloud_api.data_lake.quarantine_models import QuarantineRecord

    record = QuarantineRecord(
        quarantine_reason="not_a_real_reason",
        validation_stage="envelope_validation",
        quarantine_reference="qz-cccccccccccccccc",
        detected_at="2026-08-03T12:00:00Z",
        year="2026",
        month="08",
        day="03",
    )
    result = store.quarantine_event(record)
    assert result.status is StorageWriteStatus.REJECTED
    assert "not_a_real_reason" not in result.detail or result.detail == "QuarantineValidationError"
    assert len(result.detail) <= 64
    assert "secret" not in result.detail.lower()
