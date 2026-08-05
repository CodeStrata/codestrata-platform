"""Shared AI usage partitioning test helpers (Slice 8.8).

Not a ``test_*`` module — pytest does not collect it. Builds a fully
validated :class:`DataLakeEnvelope` for the ``ai_usage`` stream
directly from a typed endpoint request (bypassing HTTP/``app.py``
entirely), mirroring ``_extension_event_partitioning_test_helpers.py`` and
``_cli_event_partitioning_test_helpers.py``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.accepted_clock import FixedAcceptanceClock
from codestrata_platform.community_cloud_api.data_lake.envelope_builders import (
    build_data_lake_envelope,
)
from codestrata_platform.community_cloud_api.data_lake.envelopes import DataLakeEnvelope

from ._request_test_helpers import make_ai_usage_request

DEFAULT_AI_USAGE_CLOCK = FixedAcceptanceClock(
    datetime(2026, 8, 4, 0, 0, 0, tzinfo=timezone.utc)
)


def ai_usage_envelope(
    *,
    event_key: str = "event:ai-usage-partition-key",
    safe_event_reference: str = "evt-aiusagespartn",
    clock: FixedAcceptanceClock = DEFAULT_AI_USAGE_CLOCK,
    **request_overrides: Any,
) -> DataLakeEnvelope:
    """Build a validated ``ai_usage`` :class:`DataLakeEnvelope`.

    ``request_overrides`` are forwarded to
    :func:`_request_test_helpers.make_ai_usage_request`, which in
    turn forwards them to ``valid_ai_usage_body`` — pass a full
    nested block (e.g. ``usage={...}``) to override a whole section.
    """

    request = make_ai_usage_request(**request_overrides)
    return build_data_lake_envelope(
        event_stream="ai_usage",
        request=request,
        event_key=event_key,
        safe_event_reference=safe_event_reference,
        clock=clock,
    )


__all__ = ["DEFAULT_AI_USAGE_CLOCK", "ai_usage_envelope"]
