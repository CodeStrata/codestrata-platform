"""Quarantine record model tests (Slice 8.9)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.quarantine_models import (
    COMMUNITY_DATA_LAKE_QUARANTINE_SCHEMA_VERSION,
    build_quarantine_record,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_validation import (
    QuarantineValidationError,
    validate_quarantine_record,
)

from ._quarantine_test_helpers import FIXED_CLOCK, make_quarantine_record


def test_build_quarantine_record_fills_detected_at_and_date_from_clock() -> None:
    record = build_quarantine_record(
        quarantine_reason="invalid_envelope",
        validation_stage="envelope_validation",
        clock=FIXED_CLOCK,
        diagnostic_codes=("invalid_envelope",),
    )
    assert record.detected_at == "2026-08-03T12:00:00Z"
    assert (record.year, record.month, record.day) == ("2026", "08", "03")
    assert record.quarantine_schema_version == COMMUNITY_DATA_LAKE_QUARANTINE_SCHEMA_VERSION
    assert record.quarantine_reference.startswith("qz-")


def test_to_stable_dict_omits_none_optional_fields() -> None:
    record = make_quarantine_record()
    blob = record.to_stable_dict()
    assert "event_stream" not in blob
    assert "payload" not in blob
    assert "event_id" not in blob
    assert "object_key" not in blob
    assert "safe_diagnostics" not in blob


def test_validate_quarantine_record_accepts_valid_record() -> None:
    record = make_quarantine_record(event_stream="telemetry")
    assert validate_quarantine_record(record) is record


def test_validate_rejects_unknown_diagnostic_code() -> None:
    record = make_quarantine_record(diagnostic_codes=("totally_free_text_reason",))
    try:
        validate_quarantine_record(record)
        raise AssertionError("expected QuarantineValidationError")
    except QuarantineValidationError:
        pass
