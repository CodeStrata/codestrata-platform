"""Shared extension event partitioning test helpers (Slice 8.7).

Not a ``test_*`` module — pytest does not collect it. Builds a fully
validated :class:`DataLakeEnvelope` for the ``extension_event`` stream
directly from a typed endpoint request (bypassing HTTP/``app.py``
entirely), mirroring ``_cli_event_partitioning_test_helpers.py`` and
``_telemetry_partitioning_test_helpers.py``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.accepted_clock import FixedAcceptanceClock
from codestrata_platform.community_cloud_api.data_lake.envelope_builders import (
    build_data_lake_envelope,
)
from codestrata_platform.community_cloud_api.data_lake.envelopes import DataLakeEnvelope

from ._request_test_helpers import make_extension_event_request

DEFAULT_EXTENSION_EVENT_CLOCK = FixedAcceptanceClock(
    datetime(2026, 8, 4, 0, 0, 0, tzinfo=timezone.utc)
)


def extension_event_envelope(
    *,
    event_key: str = "event:extension-event-partition-key",
    safe_event_reference: str = "evt-exteventpartn",
    clock: FixedAcceptanceClock = DEFAULT_EXTENSION_EVENT_CLOCK,
    **request_overrides: Any,
) -> DataLakeEnvelope:
    """Build a validated ``extension_event`` :class:`DataLakeEnvelope`.

    ``request_overrides`` are forwarded to
    :func:`_request_test_helpers.make_extension_event_request`, which in
    turn forwards them to ``valid_extension_event_body`` — pass a full
    nested block (e.g. ``event={...}``) to override a whole section.
    """

    request = make_extension_event_request(**request_overrides)
    return build_data_lake_envelope(
        event_stream="extension_event",
        request=request,
        event_key=event_key,
        safe_event_reference=safe_event_reference,
        clock=clock,
    )


__all__ = ["DEFAULT_EXTENSION_EVENT_CLOCK", "extension_event_envelope"]
