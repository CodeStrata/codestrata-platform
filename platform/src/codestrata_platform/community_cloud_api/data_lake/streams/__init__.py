"""Per-event-stream payload projectors for Data Lake envelopes (Slice 8.3).

Each sibling module binds one :class:`~..enums.EventStream` to its endpoint
request model: a ``project_payload`` allowlisted projection function, a
``client_type_from_request`` extractor, and a stable ``SCHEMA_NAME``
constant. :mod:`..envelope_registry` imports these modules to build the
stream registry — nothing here is wired into any HTTP endpoint.
"""

from __future__ import annotations
