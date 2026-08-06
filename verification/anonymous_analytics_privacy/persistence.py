"""Persistence boundary checks (Slice 10.8)."""

from __future__ import annotations

from pathlib import Path

from codestrata.telemetry.analytics.ai_analytics import collect_ai_analytics
from codestrata.telemetry.analytics.ai_analytics_input import build_ai_analytics_input
from codestrata.telemetry.analytics.assessment_analytics import collect_assessment_analytics
from codestrata.telemetry.analytics.installation_identity import (
    new_anonymous_installation_identity,
)
from codestrata.telemetry.analytics.repository_aggregate import (
    collect_repository_aggregate_analytics,
)
from codestrata.telemetry.analytics.repository_aggregate_input import (
    build_repository_aggregate_input,
)
from codestrata.telemetry.analytics.repository_aggregate_models import (
    LanguageAggregate,
    RuleExecutionAggregate,
)
from codestrata.telemetry.analytics.runtime_analytics import collect_runtime_analytics
from verification.anonymous_analytics_privacy.engine_inputs import EngineAnalyticsInventory
from verification.anonymous_analytics_privacy.models import CheckResult, Defect
from verification.anonymous_analytics_privacy.vscode_inputs import VsCodeAnalyticsInventory


def check_persistence(
    engine: EngineAnalyticsInventory,
    vscode: VsCodeAnalyticsInventory,
    *,
    tmp_home: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    tmp_home.mkdir(parents=True, exist_ok=True)
    identity = new_anonymous_installation_identity()

    before = {p.name for p in tmp_home.iterdir()} if tmp_home.exists() else set()

    collect_runtime_analytics(
        home=tmp_home,
        identity=identity,
        cli_version="0.2.0",
        os_family="macos",
        architecture="arm64",
        runtime_version="3.12",
    )
    collect_assessment_analytics(
        home=tmp_home,
        identity=identity,
        outcome="success",
        duration_bucket="lt_1s",
    )
    collect_repository_aggregate_analytics(
        home=tmp_home,
        identity=identity,
        aggregate_input=build_repository_aggregate_input(
            language_mix=(LanguageAggregate(language_group="python", count=1),),
            rule_execution=RuleExecutionAggregate(
                attempted=1, completed=1, skipped=0, failed=0
            ),
        ),
    )
    collect_ai_analytics(
        home=tmp_home,
        identity=identity,
        aggregate=build_ai_analytics_input(
            capability="modernization_advisor",
            provider_family="openai",
            model_family="gpt_family",
            provider_ownership="customer_managed",
            outcome="success",
        ),
    )

    after = {p.name for p in tmp_home.iterdir()}
    new_files = sorted(after - before)
    # With provided identity, no files should be created.
    checks.append(
        CheckResult(
            name="persistence:no_analytics_event_files_with_identity",
            ok=new_files == [],
            detail=",".join(new_files),
            category="persistence",
            contract="engine",
        )
    )
    checks.append(
        CheckResult(
            name="persistence:base_policy_disables_event_persistence",
            ok=not engine.base_persistence_enabled,
            category="persistence",
            contract="base",
        )
    )
    checks.append(
        CheckResult(
            name="persistence:vscode_no_globalstate_writes",
            ok="globalState" not in vscode.source_blob
            and "workspaceState" not in vscode.source_blob
            and "secretStorage" not in vscode.source_blob,
            category="persistence",
            contract="vscode",
        )
    )

    for item in checks:
        if not item.ok:
            defects.append(Defect("persistence defect", item.name, "pass", "fail"))
    return checks, defects
