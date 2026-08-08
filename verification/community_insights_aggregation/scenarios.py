"""Negative scenarios A–Z."""

from __future__ import annotations

AGGREGATION_SCENARIOS: tuple[tuple[str, str], ...] = tuple(
    (chr(ord("A") + i), msg)
    for i, msg in enumerate(
        [
            "raw event count used as installation metric",
            "raw installation IDs returned",
            "S3 keys returned",
            "arbitrary metric expression accepted",
            "arbitrary S3 prefix accepted",
            "quarantine read",
            "query budget bypassed",
            "malformed object becomes zero",
            "missing identity gets fabricated",
            "report-open failure counted failed assessment",
            "activation counted VS Code usage",
            "exact model ID returned",
            "package name returned",
            "suppressed count leaked",
            "suppressed category leaked",
            "unavailable shown as zero",
            "partial shown complete",
            "UI semantics implemented in aggregation code incorrectly",
            "raw boto exception returned",
            "one failed metric destroys all valid overview results unnecessarily",
            "Redis/database added",
            "Athena/Glue added",
            "dashboard/auth package created",
            "Slice 15.8 starts",
            "verifier nondeterministic",
            "report leaks paths/keys/IDs/customer data/timestamps",
        ]
    )
)
