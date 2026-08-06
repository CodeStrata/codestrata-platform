"""Determinism checks (Slice 10.8)."""

from __future__ import annotations

from codestrata.telemetry.analytics.ai_analytics_input import build_ai_analytics_input
from codestrata.telemetry.analytics.ai_analytics_models import build_ai_analytics_event
from codestrata.telemetry.analytics.ai_analytics_serialization import (
    ai_analytics_event_to_stable_json,
)
from codestrata.telemetry.analytics.assessment_analytics import (
    build_assessment_analytics_event,
)
from codestrata.telemetry.analytics.assessment_analytics_serialization import (
    assessment_analytics_event_to_stable_json,
)
from codestrata.telemetry.analytics.installation_identity import (
    new_anonymous_installation_identity,
)
from codestrata.telemetry.analytics.policy import default_analytics_policy
from codestrata.telemetry.analytics.serialization import analytics_policy_to_stable_json
from verification.anonymous_analytics_privacy.models import CheckResult, Defect


def check_determinism() -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    policy_a = analytics_policy_to_stable_json(default_analytics_policy())
    policy_b = analytics_policy_to_stable_json(default_analytics_policy())
    checks.append(
        CheckResult(
            name="determinism:base_policy_json",
            ok=policy_a == policy_b,
            category="determinism",
            contract="base",
        )
    )

    identity = new_anonymous_installation_identity()
    # Use fixed identity value by reconstructing — compare heads reorder.
    heads_a = ("security_intelligence", "cloud_readiness")
    heads_b = ("cloud_readiness", "security_intelligence")
    ea = build_assessment_analytics_event(
        identity=identity,
        duration_bucket="lt_1s",
        outcome="success",
        enabled_assessment_heads=heads_a,
    )
    eb = build_assessment_analytics_event(
        identity=identity,
        duration_bucket="lt_1s",
        outcome="success",
        enabled_assessment_heads=heads_b,
    )
    checks.append(
        CheckResult(
            name="determinism:assessment_heads_reorder",
            ok=assessment_analytics_event_to_stable_json(ea)
            == assessment_analytics_event_to_stable_json(eb),
            category="determinism",
            contract="assessment",
        )
    )

    ai_a = build_ai_analytics_event(
        identity=identity,
        aggregate=build_ai_analytics_input(
            capability="modernization_advisor",
            provider_family="openai",
            model_family="gpt_family",
            provider_ownership="customer_managed",
            outcome="success",
        ),
    )
    ai_b = build_ai_analytics_event(
        identity=identity,
        aggregate=build_ai_analytics_input(
            capability="ai_enrichment",
            provider_family="openai",
            model_family="gpt_family",
            provider_ownership="customer_managed",
            outcome="success",
        ),
    )
    checks.append(
        CheckResult(
            name="determinism:ai_capability_alias",
            ok=ai_analytics_event_to_stable_json(ai_a)
            == ai_analytics_event_to_stable_json(ai_b),
            category="determinism",
            contract="ai",
        )
    )

    for item in checks:
        if not item.ok:
            defects.append(Defect("harness defect", item.name, "pass", "fail"))
    return checks, defects
