"""Quarantine identity tests (Slice 8.9)."""

from __future__ import annotations

from datetime import datetime, timezone

from codestrata_platform.community_cloud_api.data_lake.accepted_clock import FixedAcceptanceClock
from codestrata_platform.community_cloud_api.data_lake.quarantine_identity import (
    QUARANTINE_OBJECT_ID_PREFIX,
    build_quarantine_object_id,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_models import build_quarantine_record
from codestrata_platform.community_cloud_api.data_lake.quarantine_policy import (
    default_quarantine_policy,
)

from ._quarantine_test_helpers import make_quarantine_record

POLICY_TOKEN = default_quarantine_policy().policy_token


def test_quarantine_object_id_uses_quarantine_prefix_and_24_hex() -> None:
    record = make_quarantine_record()
    object_id = build_quarantine_object_id(record, policy_token=POLICY_TOKEN)
    assert object_id.startswith(QUARANTINE_OBJECT_ID_PREFIX)
    hex_part = object_id[len(QUARANTINE_OBJECT_ID_PREFIX) :]
    assert len(hex_part) == 24
    assert all(ch in "0123456789abcdef" for ch in hex_part)


def test_same_logical_rejection_same_id_across_dates() -> None:
    early = build_quarantine_record(
        quarantine_reason="unsafe_payload",
        validation_stage="envelope_validation",
        diagnostic_codes=("unsafe_payload",),
        clock=FixedAcceptanceClock(datetime(2026, 8, 3, 12, 0, 0, tzinfo=timezone.utc)),
    )
    late = build_quarantine_record(
        quarantine_reason="unsafe_payload",
        validation_stage="envelope_validation",
        diagnostic_codes=("unsafe_payload",),
        clock=FixedAcceptanceClock(datetime(2026, 9, 15, 8, 0, 0, tzinfo=timezone.utc)),
    )
    assert early.year != late.year or early.month != late.month or early.day != late.day
    first = build_quarantine_object_id(early, policy_token=POLICY_TOKEN)
    second = build_quarantine_object_id(late, policy_token=POLICY_TOKEN)
    assert first == second
    assert early.detected_at != late.detected_at


def test_diagnostic_codes_affect_identity() -> None:
    a = make_quarantine_record(diagnostic_codes=("unsafe_payload",))
    b = make_quarantine_record(diagnostic_codes=("invalid_envelope",))
    assert build_quarantine_object_id(a, policy_token=POLICY_TOKEN) != build_quarantine_object_id(
        b, policy_token=POLICY_TOKEN
    )


def test_detected_at_not_in_identity() -> None:
    a = make_quarantine_record(detected_at="2026-08-03T12:00:00Z", year="2026", month="08", day="03")
    b = make_quarantine_record(detected_at="2026-08-03T18:00:00Z", year="2026", month="08", day="03")
    assert build_quarantine_object_id(a, policy_token=POLICY_TOKEN) == build_quarantine_object_id(
        b, policy_token=POLICY_TOKEN
    )
