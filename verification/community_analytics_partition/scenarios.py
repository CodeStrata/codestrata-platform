"""Negative scenarios for Slice 15.2."""

from __future__ import annotations

PARTITION_SCENARIOS: tuple[tuple[str, str], ...] = (
    ("A", "analytics partition policy missing"),
    ("B", "partition redesign claimed required without proof"),
    ("C", "path dimensions diverge from 15.1 baseline"),
    ("D", "installation_id added as path dimension"),
    ("E", "metric matrix incomplete"),
    ("F", "validation dataset classified as lake-supported"),
    ("G", "bounded query model absent"),
    ("H", "backward compatibility broken"),
    ("I", "ingestion/schema change introduced"),
    ("J", "Slice 15.7 started"),
    ("K", "aggregations built in 15.2"),
    ("L", "dashboard UI package present"),
    ("M", "report nondeterministic"),
    ("N", "report leaks paths/timestamps"),
    ("O", "privacy-forbidden fields promoted to path"),
)
