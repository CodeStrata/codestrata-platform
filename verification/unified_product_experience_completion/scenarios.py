"""Negative scenarios A–Z for Slice 14.14."""

from __future__ import annotations

COMPLETION_SCENARIOS: tuple[tuple[str, str], ...] = (
    ("A", "any Slice 14 verifier missing"),
    ("B", "any Slice 14 verifier failing"),
    ("C", "any slice remains not started"),
    ("D", "Design System authority conflicts"),
    ("E", "Assessment schema not 1.2"),
    ("F", "EIR schema changed accidentally"),
    ("G", "VS Code no longer 0.2.0"),
    ("H", "active amber branding returns"),
    ("I", "Community docs expose commercial product"),
    ("J", "Marketplace exposes commercial EIR"),
    ("K", "report IA regresses"),
    ("L", "status/risk semantics regress"),
    ("M", "a11y serious regression"),
    ("N", "docs deploy path mismatch returns"),
    ("O", "Wrangler auto-setup returns"),
    ("P", "Assessment parity failure reflects real missing report content"),
    ("Q", "stale parity test forces report heading rollback"),
    ("R", "old historic verifier rewritten as current truth unnecessarily"),
    ("S", "source-locality regression"),
    ("T", "telemetry/privacy regression"),
    ("U", "current package includes Cursor"),
    ("V", "production deploy performed"),
    ("W", "release tag created"),
    ("X", "Epic 15 starts"),
    ("Y", "completion report nondeterministic"),
    ("Z", "report leaks paths/user/customer/timestamps"),
)

NEGATIVE_COMPLETION_CHECKS: tuple[str, ...] = tuple(
    f"scenario:{letter}" for letter, _ in COMPLETION_SCENARIOS
)
