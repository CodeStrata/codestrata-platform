"""Focused static checks for Slice 13.9 telemetry consent integration."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.vscode_telemetry_consent_integration.contract import (
    ASSESSMENT_SCHEMA_VERSION,
    INTEGRATION_PACKAGE,
    INTEGRATION_POLICY_ID,
    INTEGRATION_POLICY_VERSION,
    INTENDED_VSCODE_VERSION,
    RUNTIME_POLICY_ID,
    RUNTIME_POLICY_VERSION,
)
from verification.vscode_telemetry_consent_integration.models import CheckResult, Defect


def _read(monorepo: Path, relative: str) -> str:
    return (monorepo / relative).read_text(encoding="utf-8")


def _pkg_version(monorepo: Path) -> str:
    text = _read(monorepo, "vscode-plugin/package.json")
    match = re.search(r'"version"\s*:\s*"([^"]+)"', text)
    return match.group(1) if match else ""


def _extract_assess_handler(ext: str) -> str:
    """Bound extract around readiness→consent call site (not import)."""
    marker = "assertConsentMayProceed({"
    if marker not in ext:
        return ""
    idx = ext.find(marker)
    return ext[max(0, idx - 2500) : idx + 3500]


def check_all(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    policy = _read(monorepo, f"{INTEGRATION_PACKAGE}/policy.ts")
    eligibility = _read(monorepo, f"{INTEGRATION_PACKAGE}/eligibility.ts")
    ordering = _read(monorepo, f"{INTEGRATION_PACKAGE}/ordering.ts")
    diagnostics = _read(monorepo, f"{INTEGRATION_PACKAGE}/diagnostics.ts")
    asserts = _read(monorepo, f"{INTEGRATION_PACKAGE}/assert.ts")
    ext = _read(monorepo, "vscode-plugin/src/extension.ts")
    prompt_policy = _read(monorepo, "vscode-plugin/src/telemetry/promptPolicy.ts")
    prompt = _read(monorepo, "vscode-plugin/src/telemetry/prompt.ts")
    consent = _read(monorepo, "vscode-plugin/src/telemetry/consent.ts")
    runtime = _read(monorepo, "vscode-plugin/src/telemetry/runtimePolicy.ts")
    analytics_consent = _read(
        monorepo, "vscode-plugin/src/telemetry/analytics/consent.ts"
    )
    recovery = _read(monorepo, "vscode-plugin/src/failureRecovery/categories.ts")
    docs = _read(monorepo, "vscode-plugin/docs/telemetry-consent-integration.md")
    assess_region = _extract_assess_handler(ext)
    consent_call_idx = ext.find("assertConsentMayProceed({")
    ai_confirm_idx = ext.find("Continue with optional AI")

    open_handler = ""
    if 'registerCommand("codestrata.openHtmlReport"' in ext:
        start = ext.find('registerCommand("codestrata.openHtmlReport"')
        paren = ext.find("(", start)
        depth = 0
        end = paren
        for idx in range(paren, len(ext)):
            ch = ext[idx]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    end = idx + 1
                    break
        open_handler = ext[start:end]

    init_handler = ""
    if 'registerCommand("codestrata.init"' in ext:
        start = ext.find('registerCommand("codestrata.init"')
        paren = ext.find("(", start)
        depth = 0
        end = paren
        for idx in range(paren, len(ext)):
            ch = ext[idx]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    end = idx + 1
                    break
        init_handler = ext[start:end]

    activate_region = ext.split("export async function activate", 1)[0][
        :500
    ] + ext.split("export async function activate", 1)[-1][:2000]

    checks.extend(
        [
            CheckResult(
                "policy:id_version",
                INTEGRATION_POLICY_ID in policy
                and INTEGRATION_POLICY_VERSION in policy,
                f"{INTEGRATION_POLICY_ID}:{INTEGRATION_POLICY_VERSION}",
                "integration_policy",
            ),
            CheckResult(
                "runtime:relationship",
                RUNTIME_POLICY_ID in runtime
                and RUNTIME_POLICY_VERSION in runtime
                and "telemetry_runtime_policy_version: \"1.0\"" in policy,
                "runtime policy remains 1.0",
                "runtime_relationship",
            ),
            CheckResult(
                "eligibility:closed_set",
                '"codestrata.assess"' in eligibility
                and '"codestrata.assessWithAi"' in eligibility
                and "run_assessment" in eligibility
                and "ELIGIBLE_TELEMETRY_COMMANDS" in prompt_policy,
                "assess commands only",
                "eligibility",
            ),
            CheckResult(
                "eligibility:exclusions",
                '"codestrata.init"' in prompt_policy
                and '"codestrata.openHtmlReport"' in prompt_policy
                and '"activation"' in prompt_policy
                and "initialization_eligible: false" in policy,
                "ineligible surfaces",
                "eligibility",
            ),
            CheckResult(
                "ordering:stages",
                "workspace" in ordering
                and "repository_initialization" in ordering
                and "compatible_cli" in ordering
                and "ai_confirmation" in ordering
                and "telemetry_consent" in ordering,
                "readiness stages",
                "readiness_ordering",
            ),
            CheckResult(
                "ordering:extension_assert",
                "assertConsentMayProceed({" in ext
                and "resolveEngine" in assess_region
                and "Continue with optional AI" in ext,
                "consent after readiness",
                "readiness_ordering",
            ),
            CheckResult(
                "ordering:ai_before_consent",
                ai_confirm_idx != -1
                and consent_call_idx != -1
                and ai_confirm_idx < consent_call_idx,
                "AI confirm before consent",
                "readiness_ordering",
            ),
            CheckResult(
                "prompt:allow_deny",
                '"Allow"' in prompt
                and '"Deny"' in prompt
                and "Nothing is saved" in prompt,
                "Allow/Deny prompt",
                "consent_prompt",
            ),
            CheckResult(
                "prompt:default_deny",
                "denyForSession" in prompt and "user_dismiss" in prompt,
                "dismiss is Deny",
                "consent_prompt",
            ),
            CheckResult(
                "scope:command_local",
                'scope: "command"' in consent
                and "priorConsentReused: false" in consent
                and "persisted: false" in consent
                and "assertFreshConsentDecision" in asserts,
                "command-local fresh decision",
                "consent_scope",
            ),
            CheckResult(
                "non_interactive:env",
                "CODESTRATA_VSCODE_TELEMETRY_NON_INTERACTIVE" in ext
                and "non_interactive_prompt_allowed: false" in policy,
                "non-interactive suppression",
                "non_interactive",
            ),
            CheckResult(
                "allow:no_http",
                "unavailable_transport_required: true" in policy
                and "UnavailableExtensionTelemetryTransport"
                in _read(monorepo, "vscode-plugin/src/telemetry/unavailableTransport.ts"),
                "Allow keeps transport unavailable",
                "allow",
            ),
            CheckResult(
                "deny:assessment_continues",
                "denied_for_session" in consent
                and "runCommandWithTelemetryIsolation" in ext,
                "Deny does not block assessment",
                "deny",
            ),
            CheckResult(
                "analytics:gated",
                "allowed_for_session" in analytics_consent
                and "analytics_requires_allowed_consent: true" in policy,
                "analytics requires Allow",
                "analytics_integration",
            ),
            CheckResult(
                "lifecycle:event_types",
                "feature_invoked" in _read(monorepo, "vscode-plugin/src/telemetry/events.ts")
                and "feature_completed"
                in _read(monorepo, "vscode-plugin/src/telemetry/events.ts")
                and "operation_failed"
                in _read(monorepo, "vscode-plugin/src/telemetry/events.ts"),
                "bounded event types",
                "telemetry_lifecycle",
            ),
            CheckResult(
                "primary:isolation",
                "failSilentIsolation" in runtime
                or "fail_silent_isolation" in runtime,
                "telemetry fail-soft",
                "primary_authority",
            ),
            CheckResult(
                "report:ineligible",
                "report_open_eligible: false" in policy
                and "runTelemetryConsentPrompt" not in open_handler,
                "openHtmlReport no consent",
                "report_boundary",
            ),
            CheckResult(
                "recovery:ineligible",
                "recovery_eligible: false" in policy
                and "codestrata.assess" in recovery
                and "Initialize Repository" in recovery,
                "recovery actions ineligible; re-assess is new command",
                "recovery_boundary",
            ),
            CheckResult(
                "init_install:ineligible",
                "runTelemetryConsentPrompt" not in init_handler
                and "initialization_eligible: false" in policy
                and "installation_guidance_eligible: false" in policy,
                "init/install no consent",
                "init_install_discovery",
            ),
            CheckResult(
                "activation:no_prompt",
                "runTelemetryConsentPrompt" not in activate_region.split("registerCommand")[0]
                if "registerCommand" in activate_region
                else "runTelemetryConsentPrompt" not in activate_region[:800],
                "activation no consent",
                "activation",
            ),
            CheckResult(
                "persistence:forbidden",
                "persistence_allowed: false" in policy
                and "Never persisted" in consent,
                "no consent persistence",
                "persistence",
            ),
            CheckResult(
                "identity:forbidden",
                "machine_identity_allowed: false" in policy
                and "installation_identity_allowed: false" in policy
                and "machineId" not in ext,
                "no machine/install identity",
                "identity",
            ),
            CheckResult(
                "transport:unavailable",
                "defaultUnavailableTransport" in ext
                and "fetch(" not in _read(
                    monorepo, "vscode-plugin/src/telemetry/unavailableTransport.ts"
                ),
                "unavailable transport",
                "transport",
            ),
            CheckResult(
                "privacy:diagnostics",
                "integrationDiagnosticsContainForbiddenKeys" in diagnostics,
                "privacy helper",
                "privacy",
            ),
            CheckResult(
                "diagnostics:fields",
                "consent_reused: false" in diagnostics
                and "identity_used: false" in diagnostics,
                "integration diagnostics",
                "diagnostics",
            ),
            CheckResult(
                "cross_client:independent",
                (monorepo / "verification" / "privacy_first_telemetry").is_dir()
                and "community-vscode-telemetry-event-schema" in runtime,
                "VS Code schema independent",
                "cross_client_relationship",
            ),
            CheckResult(
                "docs:present",
                (monorepo / "vscode-plugin/docs/telemetry-consent-integration.md").is_file()
                and "readiness" in docs.lower()
                and "Deny" in docs,
                "docs present",
                "privacy",
            ),
            CheckResult(
                "vscode:version",
                _pkg_version(monorepo) == INTENDED_VSCODE_VERSION,
                _pkg_version(monorepo),
                "vscode_regression",
            ),
            CheckResult(
                "schema:assessment_1_2",
                ASSESSMENT_SCHEMA_VERSION == "1.2",
                ASSESSMENT_SCHEMA_VERSION,
                "vscode_regression",
            ),
            CheckResult(
                "epic_14:not_started",
                not (monorepo / "verification" / "vscode_epic14_product_experience").exists()
                and "startEpic14ProductExperience" not in ext,
                "Epic 14 deferred",
                "vscode_regression",
            ),
            CheckResult(
                "package:test_wired",
                "telemetryConsentIntegration.test.js"
                in _read(monorepo, "vscode-plugin/package.json"),
                "unit test wired",
                "vscode_regression",
            ),
            CheckResult(
                "prior_policies:recovery_1_0",
                'RECOVERY_POLICY_VERSION = "1.0"'
                in _read(monorepo, "vscode-plugin/src/failureRecovery/policy.ts"),
                "recovery policy 1.0",
                "vscode_regression",
            ),
        ]
    )

    if not all(c.ok for c in checks if c.category == "readiness_ordering"):
        defects.append(
            Defect(
                "readiness-ordering defect",
                "consent_order",
                "after readiness",
                "early consent",
            )
        )
    if not all(c.ok for c in checks if c.category == "persistence"):
        defects.append(
            Defect(
                "persistence defect",
                "consent",
                "ephemeral",
                "persisted",
            )
        )

    _ = json.loads(_read(monorepo, "vscode-plugin/package.json"))
    return checks, defects
