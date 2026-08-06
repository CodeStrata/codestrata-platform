"""Deterministic Epic 10 analytics + verification schema registry (Slice 10.9)."""

from __future__ import annotations

from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION
from codestrata.telemetry.analytics.ai_analytics_policy import (
    COMMUNITY_AI_ANALYTICS_SCHEMA_URN,
)
from codestrata.telemetry.analytics.assessment_analytics_policy import (
    COMMUNITY_ASSESSMENT_ANALYTICS_SCHEMA_URN,
)
from codestrata.telemetry.analytics.installation_identity_policy import (
    COMMUNITY_ANONYMOUS_INSTALLATION_IDENTITY_SCHEMA_URN,
)
from codestrata.telemetry.analytics.policy import (
    COMMUNITY_ANONYMOUS_ANALYTICS_SCHEMA_URN,
)
from codestrata.telemetry.analytics.repository_aggregate_policy import (
    COMMUNITY_REPOSITORY_AGGREGATE_ANALYTICS_SCHEMA_URN,
)
from codestrata.telemetry.analytics.runtime_analytics import (
    COMMUNITY_RUNTIME_ANALYTICS_SCHEMA_URN,
)
from codestrata.telemetry.runtime_policy import PRIVACY_SAFE_RUNTIME_EVENT_SCHEMA_URN
from verification.anonymous_analytics_completion.inventory import (
    EngineAnalyticsInventory,
    VsCodeAnalyticsInventory,
)
from verification.anonymous_analytics_completion.models import CheckResult, Defect

_PRIVACY_VERIFICATION_SCHEMA = "anonymous-analytics-privacy-verification:1.0.0"
_COMPLETION_VERIFICATION_SCHEMA = "anonymous-analytics-completion-verification:1.0.0"
_ASSESSMENT_REPORT_SCHEMA = f"Assessment report:{ASSESSMENT_JSON_SCHEMA_VERSION}"


def build_schema_registry() -> dict[str, str]:
    return {
        "engine.base_analytics_schema": COMMUNITY_ANONYMOUS_ANALYTICS_SCHEMA_URN,
        "engine.installation_identity_schema": (
            COMMUNITY_ANONYMOUS_INSTALLATION_IDENTITY_SCHEMA_URN
        ),
        "engine.runtime_analytics_schema": COMMUNITY_RUNTIME_ANALYTICS_SCHEMA_URN,
        "engine.assessment_analytics_schema": COMMUNITY_ASSESSMENT_ANALYTICS_SCHEMA_URN,
        "engine.repository_aggregate_analytics_schema": (
            COMMUNITY_REPOSITORY_AGGREGATE_ANALYTICS_SCHEMA_URN
        ),
        "engine.ai_analytics_schema": COMMUNITY_AI_ANALYTICS_SCHEMA_URN,
        "engine.telemetry_runtime_event_schema": PRIVACY_SAFE_RUNTIME_EVENT_SCHEMA_URN,
        "verification.anonymous_analytics_privacy_schema": _PRIVACY_VERIFICATION_SCHEMA,
        "verification.anonymous_analytics_completion_schema": (
            _COMPLETION_VERIFICATION_SCHEMA
        ),
        "product.assessment_report_schema": _ASSESSMENT_REPORT_SCHEMA,
    }


def check_schemas(
    engine: EngineAnalyticsInventory,
    vscode: VsCodeAnalyticsInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    registry = build_schema_registry()
    # VS Code schema is checked for independence, not membership (it is
    # versioned/parsed separately from the TypeScript source tree).
    registry_with_vscode = dict(registry)
    registry_with_vscode["vscode.analytics_schema"] = vscode.schema_urn

    checks.append(
        CheckResult(
            name="schema:registry_count_10",
            ok=len(registry) == 10,
            detail=f"count={len(registry)}",
            category="schema",
        )
    )
    for key, urn in sorted(registry_with_vscode.items()):
        ok = bool(urn)
        checks.append(
            CheckResult(
                name=f"schema:present:{key}",
                ok=ok,
                detail=urn,
                category="schema",
            )
        )
        if not ok:
            defects.append(Defect("documentation defect", key, "present", "missing"))

    checks.append(
        CheckResult(
            name="schema:base_schema_1_0",
            ok=registry["engine.base_analytics_schema"].endswith(":1.0"),
            detail=registry["engine.base_analytics_schema"],
            category="schema",
        )
    )
    checks.append(
        CheckResult(
            name="schema:engine_vscode_independent",
            ok=engine.base_schema_urn != vscode.schema_urn,
            detail=f"{engine.base_schema_urn} != {vscode.schema_urn}",
            category="schema",
        )
    )
    if engine.base_schema_urn == vscode.schema_urn:
        defects.append(
            Defect(
                "boundary defect",
                "schema_independence",
                "distinct schema tokens",
                "identical",
            )
        )
    _assessment_unchanged = ASSESSMENT_JSON_SCHEMA_VERSION == "1.2"
    checks.append(
        CheckResult(
            name="schema:assessment_report_unchanged_1_2",
            ok=_assessment_unchanged,
            detail=ASSESSMENT_JSON_SCHEMA_VERSION,
            category="schema",
        )
    )
    if not _assessment_unchanged:
        defects.append(
            Defect(
                "documentation defect",
                "assessment_report_schema",
                "1.2",
                ASSESSMENT_JSON_SCHEMA_VERSION,
            )
        )

    _runtime_event_unchanged = (
        PRIVACY_SAFE_RUNTIME_EVENT_SCHEMA_URN == "community-telemetry-runtime-event:1.0"
    )
    checks.append(
        CheckResult(
            name="schema:telemetry_runtime_event_unchanged_1_0",
            ok=_runtime_event_unchanged,
            detail=PRIVACY_SAFE_RUNTIME_EVENT_SCHEMA_URN,
            category="schema",
        )
    )
    if not _runtime_event_unchanged:
        defects.append(
            Defect(
                "documentation defect",
                "telemetry_runtime_event_schema",
                "community-telemetry-runtime-event:1.0",
                PRIVACY_SAFE_RUNTIME_EVENT_SCHEMA_URN,
            )
        )

    _verification_schemas_ok = registry[
        "verification.anonymous_analytics_privacy_schema"
    ].endswith(":1.0.0") and registry[
        "verification.anonymous_analytics_completion_schema"
    ].endswith(":1.0.0")
    checks.append(
        CheckResult(
            name="schema:verification_schemas_1_0_0",
            ok=_verification_schemas_ok,
            category="schema",
        )
    )
    if not _verification_schemas_ok:
        defects.append(
            Defect(
                "documentation defect",
                "verification_schemas",
                "1.0.0",
                "mismatch",
            )
        )

    return checks, defects
