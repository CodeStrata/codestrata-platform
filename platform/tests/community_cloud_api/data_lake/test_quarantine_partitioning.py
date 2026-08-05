"""Quarantine partition / object-key tests (Slice 8.9)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.identifiers import build_opaque_object_filename
from codestrata_platform.community_cloud_api.data_lake.partitions import build_quarantine_object_key
from codestrata_platform.community_cloud_api.data_lake.quarantine_identity import (
    build_quarantine_object_id,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_policy import (
    default_quarantine_policy,
)

from ._quarantine_test_helpers import make_quarantine_record

POLICY_TOKEN = default_quarantine_policy().policy_token


def test_quarantine_key_uses_reason_date_and_opaque_hex() -> None:
    record = make_quarantine_record(quarantine_reason="invalid_envelope")
    object_id = build_quarantine_object_id(record, policy_token=POLICY_TOKEN)
    key = build_quarantine_object_key(
        record.quarantine_reason, record.year, record.month, record.day, object_id
    )
    hex_part = object_id.split(":", 1)[1]
    assert key == (
        f"quarantine/reason=invalid_envelope/year=2026/month=08/day=03/{hex_part}.json"
    )
    assert "evt-" not in key
    assert "stream=" not in key


def test_opaque_filename_accepts_quarantine_object_prefix() -> None:
    record = make_quarantine_record()
    object_id = build_quarantine_object_id(record, policy_token=POLICY_TOKEN)
    assert build_opaque_object_filename(object_id) == f"{object_id.split(':', 1)[1]}.json"


def test_same_id_different_dates_produce_different_keys() -> None:
    from datetime import datetime, timezone

    from codestrata_platform.community_cloud_api.data_lake.accepted_clock import FixedAcceptanceClock
    from codestrata_platform.community_cloud_api.data_lake.quarantine_models import (
        build_quarantine_record,
    )

    early = build_quarantine_record(
        quarantine_reason="unsafe_payload",
        validation_stage="envelope_validation",
        diagnostic_codes=("unsafe_payload",),
        clock=FixedAcceptanceClock(datetime(2026, 8, 3, tzinfo=timezone.utc)),
    )
    late = build_quarantine_record(
        quarantine_reason="unsafe_payload",
        validation_stage="envelope_validation",
        diagnostic_codes=("unsafe_payload",),
        clock=FixedAcceptanceClock(datetime(2026, 9, 15, tzinfo=timezone.utc)),
    )
    early_id = build_quarantine_object_id(early, policy_token=POLICY_TOKEN)
    late_id = build_quarantine_object_id(late, policy_token=POLICY_TOKEN)
    assert early_id == late_id
    early_key = build_quarantine_object_key(
        early.quarantine_reason, early.year, early.month, early.day, early_id
    )
    late_key = build_quarantine_object_key(
        late.quarantine_reason, late.year, late.month, late.day, late_id
    )
    assert early_key != late_key
