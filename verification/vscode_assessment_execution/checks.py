"""Focused static checks for Slice 13.5 assessment execution."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.vscode_assessment_execution.contract import (
    ASSESSMENT_PACKAGE,
    ASSESSMENT_POLICY_ID,
    ASSESSMENT_POLICY_VERSION,
    ASSESSMENT_SCHEMA_VERSION,
    DISCOVERY_POLICY_VERSION,
    ENGINE_ASSESS,
    INIT_POLICY_VERSION,
    INSTALLATION_POLICY_VERSION,
    INTENDED_VSCODE_VERSION,
    WORKFLOW_POLICY_VERSION,
)
from verification.vscode_assessment_execution.models import CheckResult, Defect


def _read(monorepo: Path, relative: str) -> str:
    return (monorepo / relative).read_text(encoding="utf-8")


def _pkg_version(monorepo: Path) -> str:
    text = _read(monorepo, "vscode-plugin/package.json")
    match = re.search(r'"version"\s*:\s*"([^"]+)"', text)
    return match.group(1) if match else ""


def check_all(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    policy = _read(monorepo, f"{ASSESSMENT_PACKAGE}/policy.ts")
    orchestration = _read(monorepo, f"{ASSESSMENT_PACKAGE}/orchestration.ts")
    results = _read(monorepo, f"{ASSESSMENT_PACKAGE}/results.ts")
    diagnostics = _read(monorepo, f"{ASSESSMENT_PACKAGE}/diagnostics.ts")
    ext = _read(monorepo, "vscode-plugin/src/extension.ts")
    cli_contract = _read(monorepo, "vscode-plugin/src/engine/cliContract.ts")
    cli_runner = _read(monorepo, "vscode-plugin/src/engine/cliRunner.ts")
    prompt_policy = _read(monorepo, "vscode-plugin/src/telemetry/promptPolicy.ts")
    engine_assess = _read(monorepo, ENGINE_ASSESS)
    pkg = json.loads(_read(monorepo, "vscode-plugin/package.json"))
    docs = _read(monorepo, "vscode-plugin/docs/assessment-execution.md")
    workflow_docs = _read(monorepo, "vscode-plugin/docs/community-workflow.md")

    assess_handler = ""
    if "const runAssessment = async" in ext:
        rest = ext.split("const runAssessment = async", 1)[1]
        # Bound to the assess function body (exclude later command registrations).
        end = rest.find("const onboardingDeps")
        assess_handler = rest[:end] if end != -1 else rest[:18000]

    commands = {
        c.get("command")
        for c in pkg.get("contributes", {}).get("commands", [])
    }

    checks.extend(
        [
            CheckResult(
                "policy:id_version",
                ASSESSMENT_POLICY_ID in policy
                and ASSESSMENT_POLICY_VERSION in policy,
                f"{ASSESSMENT_POLICY_ID}:{ASSESSMENT_POLICY_VERSION}",
                "assessment_policy",
            ),
            CheckResult(
                "policy:invocation_counts",
                "standard_product_invocation_count: 1" in policy
                and "ai_product_invocation_count: 1" in policy
                and "silent_fallback_allowed: false" in policy,
                "one invocation each; no fallback",
                "assessment_policy",
            ),
            CheckResult(
                "policy:init_required",
                "initialized_repository_required: true" in policy
                and "compatible_cli_required: true" in policy,
                "init + CLI required",
                "assessment_policy",
            ),
            CheckResult(
                "command:assess",
                "codestrata.assess" in commands,
                "standard command",
                "command_surface",
            ),
            CheckResult(
                "command:assessWithAi",
                "codestrata.assessWithAi" in commands,
                "AI command",
                "command_surface",
            ),
            CheckResult(
                "command:command_determines_ai",
                'runAssessment(false, "codestrata.assess")' in ext
                and 'runAssessment(true, "codestrata.assessWithAi")' in ext
                and "defaultNoAi" not in assess_handler.split("registerCommand")[0]
                if "registerCommand" in assess_handler
                else 'runAssessment(false, "codestrata.assess")' in ext,
                "command selects AI mode",
                "command_surface",
            ),
            CheckResult(
                "activation:no_assess",
                "runAssessment("
                not in ext.split("export function activate")[1].split(
                    "const runAssessment"
                )[0]
                if "export function activate" in ext
                and "const runAssessment" in ext
                else False,
                "activation does not assess",
                "command_surface",
            ),
            CheckResult(
                "readiness:init_before_discovery",
                "planAssessmentReadiness" in assess_handler
                and assess_handler.find("planAssessmentReadiness")
                < assess_handler.find("resolveEngine"),
                "init before CLI discovery",
                "readiness",
            ),
            CheckResult(
                "readiness:discovery_before_consent",
                assess_handler.find("resolveEngine")
                < assess_handler.find("awaiting_consent"),
                "discovery before consent",
                "readiness",
            ),
            CheckResult(
                "init:blocks_not_initialized",
                "fail_not_initialized" in orchestration
                and "repository_not_initialized" in results,
                "not initialized blocks",
                "initialization_boundary",
            ),
            CheckResult(
                "init:blocks_invalid",
                "fail_invalid_configuration" in orchestration
                and "consent_category: \"not_reached\"" in orchestration.replace("'", '"')
                or "consent_category: \"not_reached\"" in orchestration
                or 'consent_category: "not_reached"' in orchestration,
                "invalid blocks consent",
                "initialization_boundary",
            ),
            CheckResult(
                "init:no_auto_init",
                "Do not auto" in docs.lower() or "do not auto-run init" in docs.lower()
                or "auto-run init" in docs.lower()
                or "does not auto-run init" in docs,
                "no auto init",
                "initialization_boundary",
            ),
            CheckResult(
                "standard:no_ai_flag",
                'withAi ? "--with-ai" : "--no-ai"' in cli_contract
                or 'options.withAi ? "--with-ai" : "--no-ai"' in cli_contract,
                "standard uses --no-ai",
                "standard_assessment",
            ),
            CheckResult(
                "standard:single_assess",
                'args = [\n    "assess"' in cli_contract
                or '"assess"' in cli_contract,
                "assess subcommand",
                "standard_assessment",
            ),
            CheckResult(
                "ai:with_ai_flag",
                "--with-ai" in cli_contract and "withAi" in cli_contract,
                "AI uses --with-ai",
                "ai_assessment",
            ),
            CheckResult(
                "ai:no_silent_fallback",
                "silent_fallback_allowed: false" in policy
                and "assertSingleAssessInvocationArgs" in assess_handler,
                "no silent AI→standard fallback",
                "ai_assessment",
            ),
            CheckResult(
                "engine:authoritative_exit",
                "exitCode !== 0" in assess_handler
                and "findings.length" not in assess_handler.split("exitCode !== 0")[0],
                "exit code not finding count",
                "engine_authority",
            ),
            CheckResult(
                "engine:assess_exists",
                "with_ai" in engine_assess.lower() or "--with-ai" in engine_assess,
                "Engine assess AI flags",
                "engine_authority",
            ),
            CheckResult(
                "cli:one_recordCliInvocation",
                assess_handler.count("recordCliInvocation()") == 1
                and assess_handler.count("runCodestrataCli") == 1,
                "one product invocation",
                "cli_invocation",
            ),
            CheckResult(
                "cli:shell_false",
                "shell: false" in cli_runner,
                "shell false",
                "cli_invocation",
            ),
            CheckResult(
                "consent:after_readiness",
                "planAssessmentReadiness" in assess_handler
                and "awaiting_consent" in assess_handler
                and assess_handler.find("planAssessmentReadiness")
                < assess_handler.find("runTelemetryConsentPrompt"),
                "consent after readiness",
                "consent_ordering",
            ),
            CheckResult(
                "consent:eligible_only_assess",
                "codestrata.assess" in prompt_policy
                and "codestrata.init"
                in prompt_policy.split("EXCLUDED_TELEMETRY_COMMANDS")[1][:800]
                if "EXCLUDED_TELEMETRY_COMMANDS" in prompt_policy
                else True,
                "init excluded; assess eligible",
                "consent_ordering",
            ),
            CheckResult(
                "telemetry:isolated",
                "telemetry_failure_isolated: true" in policy
                and "runCommandWithTelemetryIsolation" in assess_handler,
                "telemetry isolation",
                "telemetry_boundary",
            ),
            CheckResult(
                "analytics:isolated",
                "analytics_failure_isolated: true" in policy
                and "createIsolationSession" in assess_handler,
                "analytics isolation",
                "analytics_boundary",
            ),
            CheckResult(
                "process:cwd_workspace",
                "cwd: workspaceFolder" in assess_handler,
                "cwd is workspace",
                "process_boundary",
            ),
            CheckResult(
                "cancellation:distinct",
                "assessment_cancelled" in assess_handler
                and "cancelled" in assess_handler,
                "cancel distinct",
                "cancellation",
            ),
            CheckResult(
                "cancellation:no_retry",
                "retry" not in assess_handler.lower().split("cancelled")[1][:400]
                if "cancelled" in assess_handler.lower()
                else True,
                "no auto-retry on cancel",
                "cancellation",
            ),
            CheckResult(
                "primary:report_open_soft",
                "reportOpenFailed" in assess_handler,
                "report-open fail soft",
                "primary_authority",
            ),
            CheckResult(
                "report:missing_preserves_success",
                'status: "success"' in assess_handler
                and "report_not_found" in assess_handler
                and "report_missing" in results,
                "missing report ≠ assessment failure",
                "report_postcondition",
            ),
            CheckResult(
                "report:orchestration_model",
                "reportAvailable: false" in orchestration
                and "primary_exit_category: \"success\"" in orchestration.replace("'", '"')
                or 'primary_exit_category: "success"' in orchestration,
                "report_missing keeps success exit",
                "report_postcondition",
            ),
            CheckResult(
                "source:policy",
                "source_code_local: true" in policy
                and "repository_config_mutation_allowed: false" in policy,
                "source/config boundaries",
                "source_mutation",
            ),
            CheckResult(
                "config:no_write_in_assess",
                "writeFileSync" not in assess_handler
                and "write_minimal_config" not in assess_handler,
                "assess does not write config",
                "config_mutation",
            ),
            CheckResult(
                "git:no_ops",
                "git commit" not in assess_handler.lower()
                and "git add" not in assess_handler.lower(),
                "no git automation",
                "git_boundary",
            ),
            CheckResult(
                "network:no_fetch_in_handler",
                "fetch(" not in assess_handler
                and "https://" not in assess_handler,
                "no extension network in assess",
                "network_boundary",
            ),
            CheckResult(
                "privacy:forbidden_keys",
                "assessmentDiagnosticsContainForbiddenKeys" in diagnostics,
                "privacy helper",
                "privacy",
            ),
            CheckResult(
                "docs:assessment_execution",
                (monorepo / "vscode-plugin/docs/assessment-execution.md").is_file(),
                "docs present",
                "privacy",
            ),
            CheckResult(
                "docs:workflow_links",
                "assessment-execution" in workflow_docs
                or "13.5" in workflow_docs,
                "workflow docs updated",
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
                "policy:priors_1_0",
                WORKFLOW_POLICY_VERSION == "1.0"
                and DISCOVERY_POLICY_VERSION == "1.0"
                and INSTALLATION_POLICY_VERSION == "1.0"
                and INIT_POLICY_VERSION == "1.0",
                "prior policies 1.0",
                "vscode_regression",
            ),
            CheckResult(
                "epic_14:not_started",
                not (monorepo / "verification" / "vscode_epic14_product_experience").exists()
                and "startEpic14ProductExperience" not in ext
                and "redesignReportOpening" not in ext,
                "Epic 14 deferred",
                "vscode_regression",
            ),
            CheckResult(
                "docs:deferrals",
                "13.7" in docs and "13.8" in docs,
                "report/recovery deferred",
                "privacy",
            ),
        ]
    )

    # Soft-fix init:blocks_invalid check (messy or) — rebuild cleanly
    checks = [c for c in checks if c.name != "init:blocks_invalid"]
    checks.append(
        CheckResult(
            "init:blocks_invalid",
            "fail_invalid_configuration" in orchestration
            and 'consent_category: "not_reached"' in orchestration,
            "invalid blocks consent",
            "initialization_boundary",
        )
    )
    checks = [c for c in checks if c.name != "report:orchestration_model"]
    checks.append(
        CheckResult(
            "report:orchestration_model",
            "report_missing" in results
            and 'status: "report_missing"' in orchestration
            and 'primary_exit_category: "success"' in orchestration,
            "report_missing keeps success exit",
            "report_postcondition",
        )
    )
    checks = [c for c in checks if c.name != "init:no_auto_init"]
    checks.append(
        CheckResult(
            "init:no_auto_init",
            "automatically initialize" in docs.lower()
            or "auto-run init" in docs.lower(),
            "no auto init documented",
            "initialization_boundary",
        )
    )

    if not all(c.ok for c in checks if c.category == "readiness"):
        defects.append(
            Defect("readiness defect", "readiness", "init→cli→consent", "wrong order")
        )
    if not all(c.ok for c in checks if c.category == "cli_invocation"):
        defects.append(
            Defect(
                "CLI-invocation defect",
                "cli",
                "one shell:false assess",
                "invocation violation",
            )
        )
    if not all(c.ok for c in checks if c.category == "report_postcondition"):
        defects.append(
            Defect(
                "report-postcondition defect",
                "report",
                "missing ≠ failure",
                "rewrote success",
            )
        )

    return checks, defects
