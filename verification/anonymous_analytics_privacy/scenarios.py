"""Negative scenario matrix (Slice 10.8)."""

from __future__ import annotations

from codestrata.telemetry.analytics.ai_analytics_input import build_ai_analytics_input
from codestrata.telemetry.analytics.ai_analytics_mapping import (
    map_model_id_to_family,
    map_provider_to_family,
)
from codestrata.telemetry.analytics.ai_analytics_projection import (
    project_ai_analytics_from_mapping,
)
from codestrata.telemetry.analytics.assessment_analytics import (
    build_assessment_analytics_event,
)
from codestrata.telemetry.analytics.errors import AnalyticsError
from codestrata.telemetry.analytics.events import AnalyticsCategory
from codestrata.telemetry.analytics.installation_identity import (
    new_anonymous_installation_identity,
)
from codestrata.telemetry.analytics.projection import project_analytics_from_mapping
from codestrata.telemetry.analytics.repository_aggregate_input import (
    build_repository_aggregate_input,
)
from codestrata.telemetry.analytics.repository_aggregate_models import (
    LanguageAggregate,
    RuleExecutionAggregate,
)
from verification.anonymous_analytics_privacy.models import CheckResult, Defect
from verification.anonymous_analytics_privacy.vscode_inputs import VsCodeAnalyticsInventory


def _rejects(fn) -> bool:  # noqa: ANN001
    try:
        fn()
    except (AnalyticsError, Exception):
        return True
    return False


def check_scenarios(
    vscode: VsCodeAnalyticsInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    identity = new_anonymous_installation_identity()

    scenarios: list[tuple[str, bool]] = []

    scenarios.append(
        (
            "A_identity_not_machine_derived_format",
            identity.installation_id.count("-") == 4,
        )
    )
    scenarios.append(
        (
            "B_identity_rejected_on_base_event",
            _rejects(
                lambda: project_analytics_from_mapping(
                    {
                        "event_type": "x",
                        "category": AnalyticsCategory.RUNTIME.value,
                        "client_name": "codestrata_cli",
                        "privacy_projection_applied": True,
                        "installation_id": identity.installation_id,
                    }
                )
            ),
        )
    )
    scenarios.append(
        (
            "G_assessment_rejects_unknown_head",
            _rejects(
                lambda: build_assessment_analytics_event(
                    identity=identity,
                    duration_bucket="lt_1s",
                    outcome="success",
                    enabled_assessment_heads=("bogus_head",),
                )
            ),
        )
    )
    scenarios.append(
        (
            "N_repository_rejects_overflow_count",
            _rejects(
                lambda: build_repository_aggregate_input(
                    language_mix=(
                        LanguageAggregate(language_group="python", count=10_001),
                    ),
                    rule_execution=RuleExecutionAggregate(
                        attempted=1, completed=1, skipped=0, failed=0
                    ),
                )
            ),
        )
    )
    scenarios.append(
        (
            "Q_ai_rejects_exact_model_id",
            _rejects(
                lambda: map_model_id_to_family(
                    "anthropic.claude-3-5-sonnet-20241022-v2:0"
                )
            ),
        )
    )
    scenarios.append(
        (
            "P_ai_rejects_raw_provider_endpoint",
            _rejects(lambda: map_provider_to_family("https://api.openai.com/v1")),
        )
    )
    scenarios.append(
        (
            "O_ai_rejects_prompt_field",
            _rejects(
                lambda: project_ai_analytics_from_mapping(
                    {
                        "prompt": "secret prompt",
                        "capability": "modernization_advisor",
                    }
                )
            ),
        )
    )
    scenarios.append(
        (
            "T_vscode_no_machineId",
            not vscode.has_machine_id_reads,
        )
    )
    scenarios.append(
        (
            "U_vscode_no_engine_identity_file",
            not vscode.has_engine_identity_reads,
        )
    )
    scenarios.append(
        (
            "W_vscode_no_http",
            not vscode.has_http_imports,
        )
    )
    # Prompt field rejected on base analytics.
    scenarios.append(
        (
            "base_rejects_prompt",
            _rejects(
                lambda: project_analytics_from_mapping(
                    {
                        "event_type": "x",
                        "category": "runtime",
                        "client_name": "codestrata_cli",
                        "privacy_projection_applied": True,
                        "prompt": "hello",
                    }
                )
            ),
        )
    )

    for name, ok in scenarios:
        checks.append(
            CheckResult(
                name=f"scenario:{name}",
                ok=ok,
                category="scenarios",
                contract="epic10",
            )
        )
        if not ok:
            defects.append(Defect("privacy defect", name, "reject/pass", "accepted/fail"))

    return checks, defects
