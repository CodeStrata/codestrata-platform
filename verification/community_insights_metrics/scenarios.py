"""Negative scenarios A–Z."""

from __future__ import annotations

METRICS_SCENARIOS: tuple[tuple[str, str], ...] = tuple(
    (chr(ord("A") + i), msg)
    for i, msg in enumerate(
        [
            "installations labeled users",
            "raw event count used for installations",
            "DAU counts extension activation",
            "MAU name does not match window semantics",
            "first assessment ignores retained-history limitation",
            "report-open failure counted as assessment failure",
            "cancelled assessment counted failed without contract",
            "CLI adoption based on event volume",
            "findings used for head usage",
            "language and ecosystem conflated",
            "package names exposed",
            "provider adoption implies quality",
            "exact model ID exposed",
            "UI label says exact AI model adoption when only family collected",
            "VS Code activation counted as usage",
            "CLI/VS Code versions merged incorrectly",
            "validation growth fabricated from telemetry",
            "installation_id returned to dashboard",
            "rare categorical group exposed below privacy threshold",
            "unavailable displayed as zero",
            "partial displayed as complete",
            "UI owns metric computation",
            "aggregation/dashboard/auth code created",
            "Slice 15.7 starts",
            "verifier nondeterministic",
            "report leaks identifiers/paths/customer data/timestamps",
        ]
    )
)
