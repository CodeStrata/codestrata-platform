"""Shared telemetry partitioning test helpers (Slice 8.5).

Not a ``test_*`` module — pytest does not collect it. Builds a fully
validated :class:`DataLakeEnvelope` for the ``telemetry`` stream directly
from a typed endpoint request (bypassing HTTP/``app.py`` entirely),
mirroring ``_assessment_partitioning_test_helpers.py``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.accepted_clock import FixedAcceptanceClock
from codestrata_platform.community_cloud_api.data_lake.envelope_builders import (
    build_data_lake_envelope,
)
from codestrata_platform.community_cloud_api.data_lake.envelopes import DataLakeEnvelope

from ._request_test_helpers import make_telemetry_request

DEFAULT_TELEMETRY_CLOCK = FixedAcceptanceClock(
    datetime(2026, 8, 4, 0, 0, 0, tzinfo=timezone.utc)
)


def telemetry_envelope(
    *,
    event_key: str = "event:telemetry-partition-key",
    safe_event_reference: str = "evt-telemetrypartn",
    clock: FixedAcceptanceClock = DEFAULT_TELEMETRY_CLOCK,
    **request_overrides: Any,
) -> DataLakeEnvelope:
    """Build a validated ``telemetry`` :class:`DataLakeEnvelope`.

    ``request_overrides`` are forwarded to
    :func:`_request_test_helpers.make_telemetry_request`, which in turn
    forwards them to ``valid_telemetry_body`` — pass a full nested block
    (e.g. ``client={...}``) to override a whole section.
    """

    request = make_telemetry_request(**request_overrides)
    return build_data_lake_envelope(
        event_stream="telemetry",
        request=request,
        event_key=event_key,
        safe_event_reference=safe_event_reference,
        clock=clock,
    )


__all__ = ["DEFAULT_TELEMETRY_CLOCK", "telemetry_envelope"]
