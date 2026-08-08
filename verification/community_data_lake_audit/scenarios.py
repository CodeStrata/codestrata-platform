"""Negative scenarios for Slice 15.1."""

from __future__ import annotations

AUDIT_SCENARIOS: tuple[tuple[str, str], ...] = (
    ("A", "policy JSON missing or wrong id/version"),
    ("B", "bucket module absent"),
    ("C", "accepted/quarantine prefixes missing"),
    ("D", "stream set incomplete"),
    ("E", "Hive partition contract missing"),
    ("F", "envelope schema not 1.0"),
    ("G", "Assessment schema bumped away from 1.2"),
    ("H", "source_code allowed in lake envelope"),
    ("I", "installation_id allowed in path/metadata"),
    ("J", "personal identifiers allowed"),
    ("K", "customer source code allowed"),
    ("L", "Community Insights dashboard package started"),
    ("M", "Slice 15.2 report directory created"),
    ("N", "aggregations/APIs claimed in 15.1"),
    ("O", "public export allows platform lake paths"),
    ("P", "ingestion wire enabled"),
    ("Q", "audit classifications missing Required Change items"),
    ("R", "completion report nondeterministic"),
    ("S", "report leaks paths/timestamps"),
    ("T", "telemetry redesign performed"),
)
