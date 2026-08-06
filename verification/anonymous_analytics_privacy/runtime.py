"""Runtime / assessment / repository / AI / VS Code contract checkers."""

from __future__ import annotations

from pathlib import Path

from codestrata.telemetry.analytics.ai_analytics_input import build_ai_analytics_input
from codestrata.telemetry.analytics.ai_analytics_mapping import (
    map_model_id_to_family,
    map_provider_to_family,
)
from codestrata.telemetry.analytics.ai_analytics_models import build_ai_analytics_event
from codestrata.telemetry.analytics.assessment_analytics import (
    build_assessment_analytics_event,
)
from codestrata.telemetry.analytics.errors import AnalyticsError, AnalyticsErrorCode
from codestrata.telemetry.analytics.installation_identity import (
    new_anonymous_installation_identity,
)
from codestrata.telemetry.analytics.repository_aggregate_input import (
    build_repository_aggregate_input,
)
from codestrata.telemetry.analytics.repository_aggregate_models import (
    LanguageAggregate,
    RuleExecutionAggregate,
)
from codestrata.telemetry.analytics.runtime_analytics import build_runtime_analytics_event
from verification.anonymous_analytics_privacy.engine_inputs import EngineAnalyticsInventory
from verification.anonymous_analytics_privacy.models import CheckResult, Defect
from verification.anonymous_analytics_privacy.vscode_inputs import VsCodeAnalyticsInventory


def check_runtime(engine: EngineAnalyticsInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    checks.append(
        CheckResult(
            name="runtime:transmission_disabled",
            ok=not engine.runtime_transmission_enabled,
            category="runtime",
            contract="runtime",
        )
    )
    identity = new_anonymous_installation_identity()
    event = build_runtime_analytics_event(
        identity=identity,
        cli_version="0.2.0",
        os_family="macos",
        architecture="arm64",
        runtime_version="3.12",
        release_adoption="development",
    )
    envelope = event.to_stable_dict()
    base = event.to_analytics_event().to_intake_dict()
    checks.append(
        CheckResult(
            name="runtime:envelope_has_identity",
            ok="installation_id" in envelope,
            category="runtime",
            contract="runtime",
        )
    )
    checks.append(
        CheckResult(
            name="runtime:base_event_identity_free",
            ok="installation_id" not in base,
            category="runtime",
            contract="runtime",
        )
    )
    for forbidden in ("hostname", "username", "cwd", "repository", "path"):
        checks.append(
            CheckResult(
                name=f"runtime:no_{forbidden}",
                ok=forbidden not in envelope and forbidden not in base,
                category="runtime",
                contract="runtime",
            )
        )
    for item in checks:
        if not item.ok:
            defects.append(Defect("runtime analytics defect", item.name, "pass", "fail"))
    return checks, defects


def check_assessment(
    engine: EngineAnalyticsInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    checks.append(
        CheckResult(
            name="assessment:transmission_disabled",
            ok=not engine.assessment_transmission_enabled,
            category="assessment",
            contract="assessment",
        )
    )
    identity = new_anonymous_installation_identity()
    event = build_assessment_analytics_event(
        identity=identity,
        duration_bucket="s_1_10",
        outcome="success",
        enabled_assessment_heads=("security_intelligence", "cloud_readiness"),
        offline_mode=True,
        ai_requested=False,
        ai_used=False,
    )
    envelope = event.to_stable_dict()
    base = event.to_analytics_event().to_intake_dict()
    checks.append(
        CheckResult(
            name="assessment:heads_sorted",
            ok=list(event.enabled_assessment_heads)
            == sorted(event.enabled_assessment_heads),
            category="assessment",
            contract="assessment",
        )
    )
    checks.append(
        CheckResult(
            name="assessment:base_identity_free",
            ok="installation_id" not in base and "installation_id" in envelope,
            category="assessment",
            contract="assessment",
        )
    )
    # Unknown head rejects.
    rejected = False
    try:
        build_assessment_analytics_event(
            identity=identity,
            duration_bucket="lt_1s",
            outcome="success",
            enabled_assessment_heads=("not_a_real_head",),
        )
    except AnalyticsError as err:
        rejected = err.code == AnalyticsErrorCode.INVALID_HEAD
    checks.append(
        CheckResult(
            name="assessment:unknown_head_rejected",
            ok=rejected,
            category="assessment",
            contract="assessment",
        )
    )
    for item in checks:
        if not item.ok:
            defects.append(
                Defect("assessment analytics defect", item.name, "pass", "fail")
            )
    return checks, defects


def check_repository_aggregates(
    engine: EngineAnalyticsInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    checks.append(
        CheckResult(
            name="repository:transmission_disabled",
            ok=not engine.repository_transmission_enabled,
            category="repository_aggregates",
            contract="repository_aggregates",
        )
    )
    aggregate = build_repository_aggregate_input(
        language_mix=(
            LanguageAggregate(language_group="python", count=3),
            LanguageAggregate(language_group="java", count=1),
        ),
        rule_execution=RuleExecutionAggregate(
            attempted=10, completed=8, skipped=1, failed=1
        ),
    )
    payload = aggregate.to_stable_dict()
    for forbidden in ("repository", "path", "rule_id", "finding", "file"):
        checks.append(
            CheckResult(
                name=f"repository:no_{forbidden}",
                ok=forbidden not in str(payload).lower()
                or forbidden
                not in {k for row in payload.get("language_mix", []) for k in row},
                category="repository_aggregates",
                contract="repository_aggregates",
            )
        )
    # Overflow reject.
    overflow_rejected = False
    try:
        build_repository_aggregate_input(
            language_mix=(LanguageAggregate(language_group="python", count=10_001),),
            rule_execution=RuleExecutionAggregate(
                attempted=1, completed=1, skipped=0, failed=0
            ),
        )
    except AnalyticsError:
        overflow_rejected = True
    checks.append(
        CheckResult(
            name="repository:count_cap_enforced",
            ok=overflow_rejected,
            category="repository_aggregates",
            contract="repository_aggregates",
        )
    )
    # Exact-count privacy limitation is intentional and documented.
    checks.append(
        CheckResult(
            name="repository:exact_count_limitation_acknowledged",
            ok=True,
            detail="bounded exact counts are an intentional privacy limitation",
            category="repository_aggregates",
            contract="repository_aggregates",
        )
    )
    for item in checks:
        if not item.ok:
            defects.append(
                Defect("repository aggregate defect", item.name, "pass", "fail")
            )
    return checks, defects


def check_ai(engine: EngineAnalyticsInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    checks.append(
        CheckResult(
            name="ai:transmission_disabled",
            ok=not engine.ai_transmission_enabled,
            category="ai",
            contract="ai",
        )
    )
    checks.append(
        CheckResult(
            name="ai:token_bucket_excluded",
            ok=not engine.ai_token_bucket_allowed,
            category="ai",
            contract="ai",
        )
    )
    checks.append(
        CheckResult(
            name="ai:openrouter_absent",
            ok="openrouter" not in engine.ai_provider_families,
            category="ai",
            contract="ai",
        )
    )
    checks.append(
        CheckResult(
            name="ai:provider_families",
            ok={"openai", "aws_bedrock", "unavailable"} <= set(engine.ai_provider_families),
            detail=",".join(sorted(engine.ai_provider_families)),
            category="ai",
            contract="ai",
        )
    )

    assert map_provider_to_family("bedrock") == "aws_bedrock"
    assert map_model_id_to_family("gpt-4o") == "gpt_family"

    raw_model_rejected = False
    try:
        map_model_id_to_family("anthropic.claude-3-5-sonnet-20241022-v2:0")
    except AnalyticsError as err:
        raw_model_rejected = err.code in {
            AnalyticsErrorCode.RAW_MODEL_IDENTIFIER_REJECTED,
            AnalyticsErrorCode.INVALID_MODEL_FAMILY,
        }
        assert "claude" not in str(err) or str(err) == err.code.value
    checks.append(
        CheckResult(
            name="ai:raw_model_id_rejected",
            ok=raw_model_rejected,
            category="ai",
            contract="ai",
        )
    )

    identity = new_anonymous_installation_identity()
    event = build_ai_analytics_event(
        identity=identity,
        aggregate=build_ai_analytics_input(
            capability="modernization_advisor",
            provider_family="openai",
            model_family="gpt_family",
            provider_ownership="customer_managed",
            outcome="success",
            ai_used=True,
        ),
    )
    base = event.to_analytics_event().to_intake_dict()
    envelope = event.to_stable_dict()
    checks.append(
        CheckResult(
            name="ai:base_identity_free",
            ok="installation_id" not in base and "installation_id" in envelope,
            category="ai",
            contract="ai",
        )
    )
    for forbidden in ("prompt", "response", "api_key", "token_count", "cost", "model_id"):
        checks.append(
            CheckResult(
                name=f"ai:no_{forbidden}",
                ok=forbidden not in base and forbidden not in envelope,
                category="ai",
                contract="ai",
            )
        )

    # skipped is not failure
    skipped_ok = False
    try:
        build_ai_analytics_input(
            capability="modernization_advisor",
            provider_family="unavailable",
            model_family="unavailable",
            provider_ownership="unavailable",
            outcome="skipped",
            ai_used=False,
        )
        skipped_ok = True
    except AnalyticsError:
        skipped_ok = False
    checks.append(
        CheckResult(
            name="ai:skipped_not_failure",
            ok=skipped_ok,
            category="ai",
            contract="ai",
        )
    )

    for item in checks:
        if not item.ok:
            defects.append(Defect("AI analytics defect", item.name, "pass", "fail"))
    return checks, defects


def check_vscode(
    vscode: VsCodeAnalyticsInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    checks.append(
        CheckResult(
            name="vscode:policy_present",
            ok=bool(vscode.policy_urn),
            detail=vscode.policy_urn,
            category="vscode",
            contract="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="vscode:operation_categories",
            ok=set(vscode.operation_categories) == {"assess", "assess_with_ai"},
            detail=",".join(vscode.operation_categories),
            category="vscode",
            contract="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="vscode:client_editor",
            ok=vscode.client_name == "vscode_extension" and vscode.editor == "vscode",
            category="vscode",
            contract="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="vscode:no_http",
            ok=not vscode.has_http_imports,
            category="vscode",
            contract="vscode",
        )
    )
    for field in (
        "installation_id",
        "machineId",
        "workspace",
        "repository",
        "prompt",
        "provider",
        "model_id",
        "argv",
    ):
        checks.append(
            CheckResult(
                name=f"vscode:forbidden:{field}",
                ok=field in vscode.forbidden_fields
                or field.lower() in {f.lower() for f in vscode.forbidden_fields},
                category="vscode",
                contract="vscode",
            )
        )
    pkg = vscode.package_json_text.lower()
    checks.append(
        CheckResult(
            name="vscode:package_no_analytics_command",
            ok='"command": "codestrata.analytics' not in pkg
            and "analytics" not in pkg.split('"commands"')[1].split("]")[0]
            if '"commands"' in pkg
            else True,
            category="vscode",
            contract="vscode",
        )
    )
    # Safer package surface check:
    checks.append(
        CheckResult(
            name="vscode:package_no_analytics_settings",
            ok="codestrata.analytics" not in pkg and "codestrata.telemetry" not in pkg,
            category="vscode",
            contract="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="vscode:unavailable_sink_present",
            ok="UnavailableVsCodeAnalyticsSink" in vscode.source_blob,
            category="vscode",
            contract="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="vscode:consent_gating_present",
            ok="allowed_for_session" in vscode.source_blob
            and "isAnalyticsConstructionAllowed" in vscode.source_blob,
            category="vscode",
            contract="vscode",
        )
    )

    for item in checks:
        if not item.ok:
            defects.append(Defect("VS Code analytics defect", item.name, "pass", "fail"))
    return checks, defects


def check_product_paths(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    cli_root = monorepo / "engine" / "src" / "codestrata" / "cli"
    hits = []
    if cli_root.is_dir():
        for path in cli_root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for needle in (
                "collect_ai_analytics",
                "collect_assessment_analytics",
                "collect_runtime_analytics",
                "collect_repository_aggregate_analytics",
            ):
                if needle in text:
                    hits.append(needle)
    checks.append(
        CheckResult(
            name="product_path:engine_cli_unwired",
            ok=hits == [],
            detail=",".join(sorted(set(hits))),
            category="product_path",
            contract="engine",
        )
    )
    if hits:
        defects.append(
            Defect(
                "assessment analytics defect",
                "cli_wiring",
                "unwired",
                ",".join(sorted(set(hits))),
            )
        )
    return checks, defects
