"""Schemas module alias — policy/schema URN checks live in policies.py helpers."""

from __future__ import annotations

from verification.anonymous_analytics_privacy.contract import (
    ENGINE_AI_POLICY,
    ENGINE_ASSESSMENT_POLICY,
    ENGINE_BASE_POLICY,
    ENGINE_BASE_SCHEMA,
    ENGINE_IDENTITY_POLICY,
    ENGINE_REPO_POLICY,
    ENGINE_RUNTIME_POLICY,
    VSCODE_ANALYTICS_POLICY,
    VSCODE_ANALYTICS_SCHEMA,
)
from verification.anonymous_analytics_privacy.engine_inputs import EngineAnalyticsInventory
from verification.anonymous_analytics_privacy.models import CheckResult, Defect
from verification.anonymous_analytics_privacy.vscode_inputs import VsCodeAnalyticsInventory


def check_schemas(
    engine: EngineAnalyticsInventory,
    vscode: VsCodeAnalyticsInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    expected = {
        "base_policy": (engine.base_policy_urn, ENGINE_BASE_POLICY),
        "base_schema": (engine.base_schema_urn, ENGINE_BASE_SCHEMA),
        "identity_policy": (engine.identity_policy_urn, ENGINE_IDENTITY_POLICY),
        "runtime_policy": (engine.runtime_policy_urn, ENGINE_RUNTIME_POLICY),
        "assessment_policy": (engine.assessment_policy_urn, ENGINE_ASSESSMENT_POLICY),
        "repository_policy": (engine.repository_policy_urn, ENGINE_REPO_POLICY),
        "ai_policy": (engine.ai_policy_urn, ENGINE_AI_POLICY),
        "vscode_policy": (vscode.policy_urn, VSCODE_ANALYTICS_POLICY),
        "vscode_schema": (vscode.schema_urn, VSCODE_ANALYTICS_SCHEMA),
    }
    for name, (actual, want) in expected.items():
        ok = actual == want
        checks.append(
            CheckResult(
                name=f"schema:{name}",
                ok=ok,
                detail=f"{actual}",
                category="schema",
                contract=name.split("_")[0],
            )
        )
        if not ok:
            defects.append(
                Defect(
                    classification="base-contract defect"
                    if "base" in name
                    else "documentation defect",
                    component=name,
                    expected=want,
                    actual=actual or "missing",
                )
            )

    # Engine and VS Code schemas must remain independently versioned tokens.
    independent = engine.base_schema_urn != vscode.schema_urn
    checks.append(
        CheckResult(
            name="schema:engine_vscode_independent",
            ok=independent,
            detail="Engine and VS Code analytics schema tokens differ",
            category="schema",
        )
    )
    if not independent:
        defects.append(
            Defect(
                classification="boundary defect",
                component="schema_independence",
                expected="distinct schema tokens",
                actual="identical",
            )
        )
    return checks, defects
