"""Negative scenarios A–Z."""

from __future__ import annotations

QUERY_SCENARIOS: tuple[tuple[str, str], ...] = tuple(
    (chr(ord("A") + i), msg)
    for i, msg in enumerate(
        [
            "query lists raw/ root",
            "query lists entire bucket",
            "arbitrary caller prefix accepted",
            "quarantine queried",
            "provider put into S3 prefix",
            "installation_id put into prefix",
            "model_family put into prefix",
            "language put into prefix",
            "unsupported schema scanned",
            "malformed date accepted",
            "date span exceeds policy",
            "unlimited pagination",
            "unlimited object reads",
            "unlimited byte reads",
            "oversized object loaded",
            "lifetime query scans forever without budget",
            "first/repeat assessment query ignores history cost",
            "partial query returned as complete",
            "raw boto exception exposed",
            "writer permissions given to reader",
            "Athena introduced without need",
            "Redis/database introduced",
            "aggregation/dashboard implemented",
            "Slice 15.7 starts",
            "verifier nondeterministic",
            "report leaks paths/keys/identifiers/timestamps",
        ]
    )
)
