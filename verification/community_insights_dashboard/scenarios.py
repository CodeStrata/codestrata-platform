"""Negative scenarios A–Z."""

from __future__ import annotations

DASHBOARD_SCENARIOS: tuple[tuple[str, str], ...] = tuple(
    (chr(ord("A") + i), msg)
    for i, msg in enumerate(
        [
            "UI computes metric semantics itself",
            "Installations labeled Users or Customers",
            "Fabricated validation growth time-series chart",
            "Chart.js or remote chart CDN loaded",
            "Polling or websocket refresh of metrics",
            "Slice 15.12 verification started",
            "Production deployment enabled",
            "Production ingestion enabled for dashboard",
            "Forbidden chart library in package.json",
            "Fake time-series data generated in UI",
            "Privacy fields in dashboard source",
            "Privacy fields in synthetic fixtures",
            "Exact model_id shown in UI",
            "AI model family label not exact policy string",
            "Validation metric shown as growth chart",
            "Unavailable metric displayed as zero",
            "Suppressed small-group count leaked",
            "AWS SDK or S3 access from browser",
            "Second design system or off-token colors",
            "Mock client used as production default",
            "Auth fetch omits credentials include",
            "Overview split into per-metric polling requests",
            "Remote chart asset URLs in index or bundle",
            "Metric share recomputed after suppression in UI",
            "Verifier nondeterministic",
            "Report leaks paths/secrets/user data/timestamps",
        ]
    )
)
