"""Focused static checks for Slice 13.4 repository initialization."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.vscode_repository_initialization.contract import (
    ASSESSMENT_SCHEMA_VERSION,
    DISCOVERY_POLICY_VERSION,
    ENGINE_INIT,
    INIT_PACKAGE,
    INIT_POLICY_ID,
    INIT_POLICY_VERSION,
    INSTALLATION_POLICY_VERSION,
    INTENDED_VSCODE_VERSION,
    WORKFLOW_POLICY_VERSION,
)
from verification.vscode_repository_initialization.models import CheckResult, Defect


def _read(monorepo: Path, relative: str) -> str:
    return (monorepo / relative).read_text(encoding="utf-8")


def _pkg_version(monorepo: Path) -> str:
    text = _read(monorepo, "vscode-plugin/package.json")
    match = re.search(r'"version"\s*:\s*"([^"]+)"', text)
    return match.group(1) if match else ""


def check_all(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    policy = _read(monorepo, f"{INIT_PACKAGE}/policy.ts")
    detection = _read(monorepo, f"{INIT_PACKAGE}/detection.ts")
    orchestration = _read(monorepo, f"{INIT_PACKAGE}/orchestration.ts")
    results = _read(monorepo, f"{INIT_PACKAGE}/results.ts")
    diagnostics = _read(monorepo, f"{INIT_PACKAGE}/diagnostics.ts")
    ext = _read(monorepo, "vscode-plugin/src/extension.ts")
    cli_contract = _read(monorepo, "vscode-plugin/src/engine/cliContract.ts")
    cli_runner = _read(monorepo, "vscode-plugin/src/engine/cliRunner.ts")
    engine_init = _read(monorepo, ENGINE_INIT)
    transitions = _read(monorepo, "vscode-plugin/src/communityWorkflow/transitions.ts")
    prompt_policy = _read(monorepo, "vscode-plugin/src/telemetry/promptPolicy.ts")
    pkg = json.loads(_read(monorepo, "vscode-plugin/package.json"))
    init_docs = _read(monorepo, "vscode-plugin/docs/repository-initialization.md")
    workflow_docs = _read(monorepo, "vscode-plugin/docs/community-workflow.md")

    # Extract codestrata.init handler region (best-effort bounded).
    init_handler = ""
    if 'registerCommand("codestrata.init"' in ext:
        init_handler = ext.split('registerCommand("codestrata.init"', 1)[1][:4500]

    checks.extend(
        [
            CheckResult(
                "policy:id_version",
                INIT_POLICY_ID in policy and INIT_POLICY_VERSION in policy,
                f"{INIT_POLICY_ID}:{INIT_POLICY_VERSION}",
                "initialization_policy",
            ),
            CheckResult(
                "policy:engine_authoritative",
                "engine_cli_authoritative: true" in policy
                and "config_mutation_owned_by_engine: true" in policy,
                "engine owns config",
                "initialization_policy",
            ),
            CheckResult(
                "policy:forbidden_ops",
                "assessment_allowed: false" in policy
                and "telemetry_consent_allowed: false" in policy
                and "analytics_allowed: false" in policy
                and "ai_execution_allowed: false" in policy
                and "report_open_allowed: false" in policy
                and "automatic_overwrite_allowed: false" in policy,
                "boundaries closed",
                "initialization_policy",
            ),
            CheckResult(
                "policy:approach_a",
                "already_initialized_skips_cli: true" in policy,
                "skip CLI when initialized",
                "initialization_policy",
            ),
            CheckResult(
                "command:codestrata.init",
                any(
                    c.get("command") == "codestrata.init"
                    for c in pkg.get("contributes", {}).get("commands", [])
                ),
                "package contribution",
                "command_surface",
            ),
            CheckResult(
                "command:registered",
                'registerCommand("codestrata.init"' in ext,
                "extension registration",
                "command_surface",
            ),
            CheckResult(
                "command:uses_package",
                "planRepositoryInitialization" in init_handler
                and "detectRepositoryInitState" in init_handler
                and "resultAfterEngineInit" in init_handler,
                "wired to repositoryInitialization",
                "command_surface",
            ),
            CheckResult(
                "activation:no_init",
                'executeCommand("codestrata.init"'
                not in ext.split("export function activate")[0]
                and "planRepositoryInitialization"
                not in (
                    ext.split("export function activate")[1].split(
                        'registerCommand("codestrata.init"'
                    )[0]
                    if "export function activate" in ext
                    and 'registerCommand("codestrata.init"' in ext
                    else ""
                ),
                "activation does not run init workflow",
                "command_surface",
            ),
            CheckResult(
                "workspace:select_folder",
                "selectWorkspaceFolder" in init_handler,
                "workspace selection",
                "workspace_boundary",
            ),
            CheckResult(
                "workspace:fail_closed",
                "workspace_unavailable" in init_handler
                or "select_workspace" in init_handler,
                "no workspace fails closed",
                "workspace_boundary",
            ),
            CheckResult(
                "cli:discovery_before_init",
                "resolveEngine" in init_handler
                and "presentInstallationGuidance" in init_handler,
                "discovery then guidance",
                "cli_readiness",
            ),
            CheckResult(
                "cli:no_auto_resume",
                "Do not auto-resume init after guidance" in init_handler
                or "auto-resume" in init_handler.lower(),
                "no auto-resume after guidance",
                "cli_readiness",
            ),
            CheckResult(
                "state:closed_model",
                "not_initialized" in detection
                and "invalid_configuration" in detection
                and "partial_initialization" in detection,
                "state vocabulary",
                "state_detection",
            ),
            CheckResult(
                "state:structural_repository",
                "[repository]" in detection and "classifyConfigContents" in detection,
                "structural [repository] check",
                "state_detection",
            ),
            CheckResult(
                "engine:write_minimal_toml",
                "write_minimal_config" in engine_init
                and "MINIMAL_CODESTRATA_TOML" in engine_init,
                "Engine writes codestrata.toml",
                "engine_authority",
            ),
            CheckResult(
                "engine:force_exists_but_extension_forbids",
                "--force" in engine_init and "force_overwrite_forbidden" in detection,
                "Engine force exists; extension forbids",
                "engine_authority",
            ),
            CheckResult(
                "engine:extension_no_toml_write",
                "writeFileSync" not in init_handler
                and "MINIMAL_CODESTRATA_TOML" not in ext,
                "extension does not synthesize config",
                "engine_authority",
            ),
            CheckResult(
                "process:buildInitArgs_no_force",
                "never pass --force" in cli_contract
                and 'args = ["init"]' in cli_contract,
                "init args without force",
                "process_boundary",
            ),
            CheckResult(
                "process:shell_false",
                "shell: false" in cli_runner,
                "spawn shell false",
                "process_boundary",
            ),
            CheckResult(
                "process:one_invocation",
                "recordCliInvocation" in init_handler
                and "runCodestrataCli" in init_handler
                and init_handler.count("runCodestrataCli") == 1,
                "one product init invocation",
                "process_boundary",
            ),
            CheckResult(
                "idempotency:skip_already",
                "skip_already_initialized" in orchestration
                and "already_initialized" in results,
                "Approach A skip",
                "idempotency",
            ),
            CheckResult(
                "existing:invalid_preserved",
                "fail_invalid_existing" in orchestration
                and "inspect_existing_configuration" in orchestration,
                "invalid not overwritten",
                "existing_configuration",
            ),
            CheckResult(
                "existing:no_delete",
                "unlinkSync" not in init_handler and "rmSync" not in init_handler,
                "no delete of config",
                "existing_configuration",
            ),
            CheckResult(
                "post_init:verify",
                "resultAfterEngineInit" in orchestration
                and "verification_failed" in results
                and "detectRepositoryInitState" in init_handler,
                "post-init state verify",
                "post_init_verification",
            ),
            CheckResult(
                "source:policy_forbids",
                "source_file_mutation_allowed: false" in policy,
                "source mutation forbidden",
                "source_mutation",
            ),
            CheckResult(
                "git:no_git_ops_in_init",
                "git init" not in init_handler.lower()
                and "git commit" not in init_handler.lower(),
                "no git automation",
                "git_boundary",
            ),
            CheckResult(
                "network:local_only",
                "local_only: true" in policy
                and "fetch(" not in init_handler
                and "https://" not in init_handler,
                "local only",
                "network_boundary",
            ),
            CheckResult(
                "ai:not_invoked",
                "ai_execution_allowed: false" in policy
                and "offerOptionalAiSetup" not in init_handler
                and "with-ai" not in init_handler,
                "no AI on init",
                "ai_boundary",
            ),
            CheckResult(
                "telemetry:excluded_command",
                '"codestrata.init"' in prompt_policy
                and "ELIGIBLE_TELEMETRY_COMMANDS" in prompt_policy
                and "codestrata.init"
                not in prompt_policy.split("ELIGIBLE_TELEMETRY_COMMANDS")[1].split(
                    "]"
                )[0],
                "init not eligible",
                "telemetry_boundary",
            ),
            CheckResult(
                "telemetry:result_flags",
                "telemetry_invoked: false" in results
                or 'telemetry_invoked: false' in results,
                "result forbids telemetry",
                "telemetry_boundary",
            ),
            CheckResult(
                "analytics:forbidden",
                "analytics_allowed: false" in policy
                and ("analytics_invoked: false" in results or "analytics_invoked" in results),
                "no analytics",
                "analytics_boundary",
            ),
            CheckResult(
                "report:not_opened",
                "report_open_allowed: false" in policy
                and "openHtmlReport" not in init_handler
                and "findLatestRunDirectory" not in init_handler,
                "no report open",
                "report_boundary",
            ),
            CheckResult(
                "assessment:not_run",
                "assessment_allowed: false" in policy
                and "buildAssessArgs" not in init_handler
                and "running_assessment" not in init_handler,
                "no assessment",
                "report_boundary",
            ),
            CheckResult(
                "workflow:init_states",
                '"initializing"' in transitions
                and "validating_workspace" in transitions
                and 'validating_workspace: [' in transitions
                and "completed" in transitions.split("validating_workspace:")[1].split("],")[0],
                "init workflow edges",
                "workflow_integration",
            ),
            CheckResult(
                "workflow:no_consent_on_init",
                "awaiting_consent" not in init_handler,
                "no consent state on init",
                "workflow_integration",
            ),
            CheckResult(
                "cancellation:status",
                '"cancelled"' in results and "cancelled" in orchestration,
                "cancelled distinct",
                "cancellation",
            ),
            CheckResult(
                "privacy:forbidden_keys",
                "repoInitDiagnosticsContainForbiddenKeys" in diagnostics,
                "privacy helper",
                "privacy",
            ),
            CheckResult(
                "privacy:docs",
                "path" in init_docs.lower() and "stdout" in init_docs.lower(),
                "docs mention privacy constraints",
                "privacy",
            ),
            CheckResult(
                "docs:repository_initialization",
                (monorepo / "vscode-plugin/docs/repository-initialization.md").is_file(),
                "init docs present",
                "privacy",
            ),
            CheckResult(
                "docs:workflow_links_init",
                "repository-initialization" in workflow_docs
                or "Initialize Repository" in workflow_docs,
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
                "policy:workflow_1_0",
                WORKFLOW_POLICY_VERSION == "1.0",
                WORKFLOW_POLICY_VERSION,
                "vscode_regression",
            ),
            CheckResult(
                "policy:discovery_1_0",
                DISCOVERY_POLICY_VERSION == "1.0",
                DISCOVERY_POLICY_VERSION,
                "vscode_regression",
            ),
            CheckResult(
                "policy:installation_1_0",
                INSTALLATION_POLICY_VERSION == "1.0",
                INSTALLATION_POLICY_VERSION,
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
                "negative:no_force_in_handler",
                "--force" not in init_handler,
                "handler never passes force",
                "existing_configuration",
            ),
            CheckResult(
                "engine_compat:writes_toml_only",
                "write_text(MINIMAL_CODESTRATA_TOML" in engine_init
                and "target.parent.mkdir" in engine_init
                and "subprocess" not in engine_init
                and "git init" not in engine_init.lower()
                and "git commit" not in engine_init.lower(),
                "Engine writes toml only; no git automation",
                "engine_authority",
            ),
        ]
    )

    if not all(c.ok for c in checks if c.category == "engine_authority"):
        defects.append(
            Defect(
                "Engine-authority defect",
                "engine_authority",
                "Engine sole writer",
                "authority leak",
            )
        )
    if not all(c.ok for c in checks if c.category == "telemetry_boundary"):
        defects.append(
            Defect(
                "telemetry/analytics boundary defect",
                "telemetry",
                "no telemetry on init",
                "telemetry leak",
            )
        )
    if not all(c.ok for c in checks if c.category == "process_boundary"):
        defects.append(
            Defect(
                "process-boundary defect",
                "process",
                "one shell:false init",
                "process violation",
            )
        )

    return checks, defects
