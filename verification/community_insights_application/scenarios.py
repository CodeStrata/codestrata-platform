"""Negative scenarios A–Z."""

from __future__ import annotations

APPLICATION_SCENARIOS: tuple[tuple[str, str], ...] = tuple(
    (chr(ord("A") + i), msg)
    for i, msg in enumerate(
        [
            "UI computes metric semantics itself",
            "UI accesses S3 directly",
            "AWS SDK added to browser",
            "installation_id appears in frontend model/output",
            "raw telemetry exposed",
            "repository/path fields exposed",
            "exact model_id exposed",
            "unavailable displayed as zero",
            "suppressed hidden count leaked",
            "mock data shipped as live production data",
            "second design system created",
            "hardcoded stale brand colors",
            "commercial Platform product promoted",
            "application depends on monorepo-only runtime path",
            "exported app cannot build independently",
            "Platform backend code exported into Insights repository",
            "secrets copied into exported repo",
            "node_modules/dist exported",
            "public repo classification used for private Insights app",
            "Git init/push performed by exporter",
            "authentication implemented early",
            "Secrets Manager used from browser",
            "production deploy/DNS created",
            "Slice 15.9 starts",
            "verifier nondeterministic",
            "report leaks paths/secrets/user/customer data/timestamps",
        ]
    )
)
