"""Negative scenarios A–Z."""

from __future__ import annotations

INGESTION_SCENARIOS: tuple[tuple[str, str], ...] = tuple(
    (chr(ord("A") + i), msg)
    for i, msg in enumerate(
        [
            "repository name enters analytics",
            "repository path enters analytics",
            "file path enters analytics",
            "findings enter analytics",
            "evidence enters analytics",
            "dependency/package name enters ecosystem field",
            "arbitrary ecosystem string accepted",
            "OpenRouter endpoint enters payload",
            "OpenRouter API key env/value enters payload",
            "exact model ID enters analytics",
            "arbitrary ProviderModelReference enters model_family",
            "prompt enters AI usage",
            "response enters AI usage",
            "VS Code machineId used as installation_id",
            "VS Code creates second tracking identity without contract",
            "denied consent still sends analytics",
            "non-interactive policy changes silently",
            "transport failure breaks assessment",
            "writer failure breaks CLI",
            "raw exception appears in telemetry/report",
            "server accepts forbidden field",
            "quarantine reason includes raw sensitive value",
            "aggregation/dashboard package created",
            "Slice 15.7 starts",
            "verifier nondeterministic",
            "verification report leaks identifiers/paths/secrets/timestamps",
        ]
    )
)
