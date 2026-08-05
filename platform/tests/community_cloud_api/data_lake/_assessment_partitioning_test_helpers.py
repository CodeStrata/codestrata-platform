"""Shared assessment-metadata partitioning test helpers (Slice 8.4).

Not a ``test_*`` module — pytest does not collect it. Builds a fully
validated :class:`DataLakeEnvelope` for the ``assessment_metadata`` stream
directly from a typed endpoint request (bypassing HTTP/``app.py``
entirely), mirroring the pattern already used by
``_request_test_helpers.py`` / ``_envelope_test_helpers.py``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.accepted_clock import FixedAcceptanceClock
from codestrata_platform.community_cloud_api.data_lake.envelope_builders import (
    build_data_lake_envelope,
)
from codestrata_platform.community_cloud_api.data_lake.envelopes import DataLakeEnvelope

from ._request_test_helpers import make_assessment_metadata_request

DEFAULT_ASSESSMENT_CLOCK = FixedAcceptanceClock(
    datetime(2026, 8, 4, 0, 0, 0, tzinfo=timezone.utc)
)


def assessment_envelope(
    *,
    event_key: str = "event:assessment-partition-key",
    safe_event_reference: str = "evt-assessmentpartn",
    clock: FixedAcceptanceClock = DEFAULT_ASSESSMENT_CLOCK,
    **request_overrides: Any,
) -> DataLakeEnvelope:
    """Build a validated ``assessment_metadata`` :class:`DataLakeEnvelope`.

    ``request_overrides`` are forwarded to
    :func:`_request_test_helpers.make_assessment_metadata_request`, which in
    turn forwards them to ``valid_assessment_metadata_body`` — pass a full
    nested block (e.g. ``assessment={...}``) to override a whole section.
    """

    request = make_assessment_metadata_request(**request_overrides)
    return build_data_lake_envelope(
        event_stream="assessment_metadata",
        request=request,
        event_key=event_key,
        safe_event_reference=safe_event_reference,
        clock=clock,
    )


__all__ = ["DEFAULT_ASSESSMENT_CLOCK", "assessment_envelope"]
