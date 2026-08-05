"""Shared helpers for quarantine tests (Slice 8.9)."""

from __future__ import annotations

from datetime import datetime, timezone

from codestrata_platform.community_cloud_api.data_lake.accepted_clock import FixedAcceptanceClock
from codestrata_platform.community_cloud_api.data_lake.quarantine_models import (
    QuarantineRecord,
    build_quarantine_record,
)

FIXED_CLOCK = FixedAcceptanceClock(datetime(2026, 8, 3, 12, 0, 0, tzinfo=timezone.utc))


def make_quarantine_record(**overrides: object) -> QuarantineRecord:
    """Build a valid quarantine record with sensible defaults for tests."""

    base: dict[str, object] = {
        "quarantine_reason": "unsafe_payload",
        "validation_stage": "envelope_validation",
        "clock": FIXED_CLOCK,
        "diagnostic_codes": ("unsafe_payload",),
    }
    base.update(overrides)
    return build_quarantine_record(**base)  # type: ignore[arg-type]
