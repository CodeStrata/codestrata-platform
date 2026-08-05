"""Shared envelope-construction helper for Data Lake tests (Slice 8.1 / 8.2 / 8.3).

Not a ``test_*`` module — pytest does not collect it. Every Slice 8.1/8.2
test that previously built its own flat-shape ``_envelope()`` helper now
imports :func:`make_envelope` from here, built against the Slice 8.3 nested
envelope contract (see ``envelopes.py`` and
``platform/docs/community-cloud-api/data-lake-event-envelope.md``).
"""

from __future__ import annotations

from typing import Any

from codestrata_platform.community_cloud_api.data_lake.envelopes import (
    DataLakeEnvelope,
    build_envelope,
)

DEFAULT_ACCEPTED_AT = "2026-08-03T00:00:00Z"


def make_envelope(**overrides: Any) -> DataLakeEnvelope:
    """Build a nested-shape :class:`DataLakeEnvelope` with sensible telemetry defaults."""

    base: dict[str, Any] = dict(
        event_stream="telemetry",
        schema_name="community-telemetry",
        schema_version="1.0",
        policy_id="community-telemetry-policy:1.0",
        event_key="event:abcdef123456789012345678",
        safe_event_reference="evt-aaaaaaaaaaaa",
        accepted_at=DEFAULT_ACCEPTED_AT,
        client_type="codestrata_cli",
        payload={"duration_bucket": "1s_to_5s"},
    )
    base.update(overrides)
    policy = base.pop("policy", None)
    return build_envelope(policy=policy, **base)


__all__ = ["DEFAULT_ACCEPTED_AT", "make_envelope"]
