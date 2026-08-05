"""Deterministic acceptance-time clock for Data Lake envelope construction (Slice 8.3).

``accepted_at`` is server-assigned acceptance time, never a client-submitted
timestamp — it exists purely so archival partitions are deterministic and
reproducible from a given clock. :class:`FixedAcceptanceClock` is the
reference implementation used by every test and by any future deterministic
replay tooling; :class:`SystemAcceptanceClock` is the only clock that reads
wall time.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Protocol

_ACCEPTED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_PARTITION_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class AcceptanceClockError(ValueError):
    """Raised when acceptance-time material cannot be parsed or formatted safely."""


class AcceptanceClock(Protocol):
    """Persistence-neutral source of server acceptance time."""

    def now_utc(self) -> datetime: ...


class FixedAcceptanceClock:
    """A clock that always returns the same instant — deterministic tests/replay."""

    def __init__(self, when: datetime) -> None:
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        self._when = when.astimezone(timezone.utc)

    def now_utc(self) -> datetime:
        return self._when


class SystemAcceptanceClock:
    """Reads real wall-clock time — the only non-deterministic clock in this package."""

    def now_utc(self) -> datetime:
        return datetime.now(timezone.utc)


def format_accepted_at(dt: datetime) -> str:
    """Normalize ``dt`` to UTC and format as ``YYYY-MM-DDTHH:MM:SSZ``.

    Truncates sub-second precision for deterministic, compact envelopes —
    the Data Lake archival boundary never needs sub-second acceptance
    resolution.
    """

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def partition_date_from_accepted_at(accepted_at: str) -> str:
    """Derive the ``YYYY-MM-DD`` partition date from a formatted ``accepted_at``."""

    text = (accepted_at or "").strip()
    if not _ACCEPTED_AT_RE.match(text):
        raise AcceptanceClockError(f"invalid accepted_at: {accepted_at!r}")
    return text[:10]


def partition_components(partition_date: str) -> tuple[str, str, str]:
    """Split a ``YYYY-MM-DD`` partition date into ``(year, month, day)``."""

    text = (partition_date or "").strip()
    if not _PARTITION_DATE_RE.match(text):
        raise AcceptanceClockError(f"invalid partition_date: {partition_date!r}")
    year, month, day = text.split("-")
    return year, month, day
