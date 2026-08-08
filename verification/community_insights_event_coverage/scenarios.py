"""Negative scenarios A–Z for Slice 15.3."""

from __future__ import annotations

COVERAGE_SCENARIOS: tuple[tuple[str, str], ...] = (
    ("A", "installation count uses event count"),
    ("B", "DAU counts every raw event"),
    ("C", "first assessment flag invented unnecessarily"),
    ("D", "report-open failure counted as assessment failure"),
    ("E", "CLI version sourced from executable path"),
    ("F", "assessment-head usage captures findings/evidence"),
    ("G", "language metric captures file paths"),
    ("H", "ecosystem metric captures package names"),
    ("I", "AI provider metric captures credentials"),
    ("J", "AI model metric bypasses privacy contract"),
    ("K", "VS Code activation counted as usage without contract"),
    ("L", "release adoption creates new user identity"),
    ("M", "validation dataset growth forced into telemetry"),
    ("N", "repository name added to schema"),
    ("O", "source path added to schema"),
    ("P", "customer/org identity added"),
    ("Q", "IP/hostname collected"),
    ("R", "prompt/response collected"),
    ("S", "raw model endpoint collected"),
    ("T", "schema change activated in runtime"),
    ("U", "ingestion enabled"),
    ("V", "aggregation service created"),
    ("W", "dashboard package created"),
    ("X", "Slice 15.7 starts"),
    ("Y", "verifier nondeterministic"),
    ("Z", "report leaks identifiers/paths/customer data/timestamps"),
)
