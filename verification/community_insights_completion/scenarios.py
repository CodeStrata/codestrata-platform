"""Negative scenarios A–Z for Slice 15.12."""

from __future__ import annotations

COMPLETION_SCENARIOS: tuple[tuple[str, str], ...] = (
    ("A", "any Slice 15 verifier missing"),
    ("B", "any Slice 15 verifier failing"),
    ("C", "any slice remains not started"),
    ("D", "data lake policy drift"),
    ("E", "partition strategy drift"),
    ("F", "event coverage regression"),
    ("G", "ingestion privacy regression"),
    ("H", "bounded query strategy regression"),
    ("I", "metrics contract regression"),
    ("J", "aggregation service regression"),
    ("K", "insights application regression"),
    ("L", "authentication regression"),
    ("M", "dashboard regression"),
    ("N", "validation regression"),
    ("O", "Athena/Glue/Redis required unexpectedly"),
    ("P", "production ingestion enabled"),
    ("Q", "live dashboard data claimed"),
    ("R", "insights site deployed"),
    ("S", "real secrets configured"),
    ("T", "remote insights repository created"),
    ("U", "Epic 16 starts"),
    ("V", "production deploy performed"),
    ("W", "release tag created"),
    ("X", "source locality regression"),
    ("Y", "completion report nondeterministic"),
    ("Z", "report leaks paths/secrets/timestamps"),
)

NEGATIVE_COMPLETION_CHECKS: tuple[str, ...] = tuple(
    f"scenario:{letter}" for letter, _ in COMPLETION_SCENARIOS
)
