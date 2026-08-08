import * as fs from "node:fs";
import * as path from "node:path";

import * as vscode from "vscode";

import { readSettingsFromWorkspaceConfig, type FindingsGroupBy } from "./config/settings";
import { FindingsDiagnostics } from "./diagnostics/findingsDiagnostics";
import {
  aiOptionalGuidance,
  buildAssessArgs,
  buildDoctorArgs,
  buildInitArgs,
  ENGINE_DOCS_QUICK_START,
  ENGINE_INSTALL_HINT,
  parseJsonSummary,
} from "./engine/cliContract";
import { runCodestrataCli } from "./engine/cliRunner";
import {
  redactSecrets,
  type EngineCandidate,
} from "./engine/discovery";
import {
  createNodeProbeRunner,
  discoverCodeStrataCli,
  discoveryOutputMessage,
  workflowErrorForDiscoveryStatus,
  type CliDiscoveryStatus,
} from "./cliDiscovery";
import {
  assertInitArgsForbidForce,
  detectRepositoryInitState,
  planRepositoryInitialization,
  resultAfterEngineInit,
  resultForPlanWithoutCli,
  userMessageForInitResult,
  createRepoInitResult,
} from "./repositoryInitialization";
import {
  assertSingleAssessInvocationArgs,
  mapInitStateToWorkflowFlag,
  planAssessmentReadiness,
  resultAfterEngineAssessment,
  resultForCliUnavailable,
  resultForReadinessFailure,
  userMessageForAssessmentReadiness,
  type AssessmentConsentCategory,
  type AssessmentOperation,
} from "./assessmentExecution";
import {
  AssessmentProgressLifecycle,
  progressStatusFromPrimary,
  progressTitle,
} from "./assessmentProgress";
import {
  locateHtmlReport,
  openValidatedHtmlReport,
  resultForUserDeclined,
  userMessageForReportResult,
  type OpenHtmlAdapter,
} from "./reportOpening";
import {
  presentFailureRecovery,
  resolveRecoveryGuidance,
} from "./failureRecovery";
import { createVsCodeRecoveryHost } from "./failureRecovery/vscodeHost";
import { presentInstallationGuidance } from "./cliInstallation/vscodeHost";
import {
  guidedInstallEngine,
  maybeRunFirstRun,
  runWelcomeFlow,
  type OnboardingDeps,
} from "./onboarding/firstRun";
import {
  findLatestRunDirectory,
  loadArtifactsFromRunDirectory,
  primaryEvidenceExcerpt,
  primaryEvidencePath,
} from "./reports/parser";
import { SUPPORTED_SCHEMA_DOC } from "./reports/schema";
import type { Finding, ParsedAssessmentArtifacts } from "./reports/types";
import {
  appendOutput,
  appendOutputLine,
  disposeOutputChannel,
  showOutput,
} from "./ui/output";
import {
  ASSESSMENT_COMPLETE_DISMISS,
  ASSESSMENT_COMPLETE_MESSAGE,
  ASSESSMENT_COMPLETE_OPEN_REPORT,
} from "./ui/presentationCopy";
import { StatusBarController } from "./ui/statusBar";
import { FindingsTreeProvider } from "./views/findingsTree";
import { RecommendationsTreeProvider } from "./views/recommendationsTree";
import { extractEvidenceLine, resolveWorkspaceRelativePath } from "./workspace/paths";
import {
  createIsolationSession,
  defaultUnavailableTransport,
  runCommandWithTelemetryIsolation,
  runTelemetryConsentPrompt,
  type TelemetryPromptUi,
} from "./telemetry";
import {
  assertConsentMayProceed,
  assertFreshConsentDecision,
  createIntegrationDiagnostics,
  createTelemetryIntegrationPolicy,
  integrationDiagnosticsToStableDict,
  integrationOperationLabel,
  isTelemetryEligibleCommand,
} from "./telemetryConsentIntegration";
import {
  evaluateCliCompatibility,
  doctorCompatibilityLabel,
  userMessageForCompatibility,
} from "./cliCompatibility";
import {
  CommunityWorkflowSession,
  classifyWorkspaceKind,
  mapConsentToDecisionCategory,
} from "./communityWorkflow";

export type ResolvedEngine = EngineCandidate & {
  versionOutput?: string;
  discoveryStatus?: CliDiscoveryStatus;
  compatibilityVerdict?: string;
};

function mapDiscoverySourceToLegacy(
  source: string
): EngineCandidate["source"] {
  if (source === "explicit_configuration") {
    return "configured";
  }
  if (source === "process_path") {
    return "path";
  }
  return "workspace-venv";
}

let lastArtifacts: ParsedAssessmentArtifacts | undefined;
let assessmentInFlight = false;
let activeAbort: AbortController | undefined;

function isTelemetryInteractive(): boolean {
  const forced = process.env.CODESTRATA_VSCODE_TELEMETRY_NON_INTERACTIVE;
  if (forced === "1" || forced === "true") {
    return false;
  }
  const ci = process.env.CI;
  if (ci === "1" || ci === "true") {
    return false;
  }
  return true;
}

function createTelemetryPromptUi(): TelemetryPromptUi {
  return {
    async showConsentPrompt(message, allow, deny) {
      const choice = await vscode.window.showInformationMessage(
        message,
        allow,
        deny
      );
      if (choice === allow) {
        return "Allow";
      }
      if (choice === deny) {
        return "Deny";
      }
      return undefined;
    },
  };
}

export function activate(context: vscode.ExtensionContext): void {
  const statusBar = new StatusBarController();
  const findingsProvider = new FindingsTreeProvider();
  const recommendationsProvider = new RecommendationsTreeProvider();
  const diagnostics = new FindingsDiagnostics();

  context.subscriptions.push(
    statusBar,
    findingsProvider,
    recommendationsProvider,
    diagnostics,
    vscode.window.registerTreeDataProvider("codestrata.findings", findingsProvider),
    vscode.window.registerTreeDataProvider(
      "codestrata.recommendations",
      recommendationsProvider
    ),
    { dispose: disposeOutputChannel },
    {
      dispose: () => {
        activeAbort?.abort();
        activeAbort = undefined;
        assessmentInFlight = false;
      },
    }
  );

  const loadSettings = () =>
    readSettingsFromWorkspaceConfig((key) =>
      vscode.workspace.getConfiguration().get(key)
    );

  const clearResults = (): void => {
    lastArtifacts = undefined;
    findingsProvider.setFindings([]);
    recommendationsProvider.setRecommendations([]);
    diagnostics.clear();
    statusBar.setIdle();
  };

  const selectWorkspaceFolder = async (options?: {
    allowFallbackCwd?: boolean;
    quiet?: boolean;
  }): Promise<string | undefined> => {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders || folders.length === 0) {
      if (options?.allowFallbackCwd) {
        return process.cwd();
      }
      if (!options?.quiet) {
        void presentFailureRecovery({
          failureCategory: "workspace_unavailable",
          host: createVsCodeRecoveryHost({ appendOutputLine }),
          messageOverride:
            "CodeStrata requires an open workspace folder (local repository).",
        });
      }
      return undefined;
    }
    if (folders.length === 1) {
      return folders[0].uri.fsPath;
    }
    const picked = await vscode.window.showQuickPick(
      folders.map((folder) => ({
        label: folder.name,
        description: folder.uri.fsPath,
        folder,
      })),
      {
        title: "Select repository for CodeStrata Engineering Assessment",
        placeHolder: "Multi-root workspace — choose a folder",
      }
    );
    return picked?.folder.uri.fsPath;
  };

  const ensureTrusted = async (workspaceFolder: string): Promise<boolean> => {
    if (vscode.workspace.isTrusted) {
      return true;
    }
    const choice = await vscode.window.showWarningMessage(
      "This workspace is untrusted. CodeStrata Engine will not run against untrusted workspaces without approval.",
      "Manage Workspace Trust",
      "Cancel"
    );
    if (choice === "Manage Workspace Trust") {
      await vscode.commands.executeCommand("workbench.trust.manage");
    }
    void workspaceFolder;
    return false;
  };

  const configureExecutable = async (executable: string): Promise<void> => {
    await vscode.workspace
      .getConfiguration()
      .update(
        "codestrata.engine.executable",
        executable,
        vscode.ConfigurationTarget.Global
      );
  };

  const resolveEngine = async (
    workspaceFolder: string,
    options?: { silentMissing?: boolean; session?: CommunityWorkflowSession }
  ): Promise<ResolvedEngine | undefined> => {
    const settings = loadSettings();
    const folders =
      vscode.workspace.workspaceFolders?.map((folder) => folder.uri.fsPath) ?? [
        workspaceFolder,
      ];
    appendOutputLine("Resolving CodeStrata Engine executable…");

    const baseRunner = createNodeProbeRunner();
    const outcome = await discoverCodeStrataCli({
      configuredExecutable: settings.executable,
      workspaceFolders: folders,
      cwd: workspaceFolder,
      runner: async (request) => {
        options?.session?.recordDiscoveryProbe();
        return baseRunner(request);
      },
    });

    options?.session?.setDiscoveryStatus(outcome.public.status);
    appendOutputLine(discoveryOutputMessage(outcome.public));

    if (outcome.public.status === "compatible" && outcome.resolved) {
      const decision = evaluateCliCompatibility({
        cliVersion: outcome.resolved.version,
      });
      return {
        executable: outcome.resolved.command,
        source: mapDiscoverySourceToLegacy(outcome.resolved.source),
        versionOutput: `CodeStrata ${outcome.resolved.version}`,
        discoveryStatus: outcome.public.status,
        compatibilityVerdict: decision.verdict,
      };
    }

    if (options?.silentMissing) {
      appendOutputLine("Engine not found (silent for onboarding).");
      return undefined;
    }

    const action = await vscode.window.showErrorMessage(
      outcome.public.status === "invalid_configuration" ||
        outcome.public.status === "not_executable"
        ? "Configured CodeStrata Engine CLI could not be used."
        : outcome.public.status === "incompatible"
          ? userMessageForCompatibility(
              evaluateCliCompatibility({
                cliVersion:
                  outcome.public.version_major !== undefined &&
                  outcome.public.version_minor !== undefined &&
                  outcome.public.version_patch !== undefined
                    ? {
                        major: outcome.public.version_major,
                        minor: outcome.public.version_minor,
                        patch: outcome.public.version_patch,
                      }
                    : undefined,
              })
            )
          : outcome.public.status === "identity_mismatch"
            ? "The configured executable is not a CodeStrata CLI."
            : "CodeStrata Engine CLI was not found. This Community extension requires CodeStrata Engine.",
      "Installation Guidance…",
      "Open Installation Docs",
      "Configure Executable",
      "Show Output"
    );
    if (action === "Installation Guidance…") {
      await presentInstallationGuidance({
        discoveryStatus: outcome.public.status,
        host: {
          appendOutputLine,
          refreshDiscovery: async () => {
            const again = await resolveEngine(workspaceFolder, {
              silentMissing: true,
            });
            return again?.discoveryStatus ?? (again ? "compatible" : "not_found");
          },
        },
      });
    } else if (action === "Open Installation Docs") {
      await vscode.env.openExternal(vscode.Uri.parse(ENGINE_DOCS_QUICK_START));
    } else if (action === "Configure Executable") {
      await vscode.commands.executeCommand(
        "workbench.action.openSettings",
        "codestrata.engine.executable"
      );
    } else if (action === "Show Output") {
      showOutput(false);
    }
    appendOutputLine(ENGINE_INSTALL_HINT);
    return undefined;
  };

  const applyArtifacts = (
    workspaceFolder: string,
    artifacts: ParsedAssessmentArtifacts
  ): void => {
    lastArtifacts = artifacts;
    findingsProvider.setWorkspaceFolder(workspaceFolder);
    findingsProvider.setGroupBy(loadSettings().groupBy);
    findingsProvider.setFindings(artifacts.findings);
    recommendationsProvider.setRecommendations(artifacts.recommendations);
    diagnostics.publish(workspaceFolder, artifacts.findings);
    statusBar.setReady(artifacts.findings.length);
    for (const warning of artifacts.parseWarnings) {
      appendOutputLine(`Warning: ${warning}`);
    }
    if (artifacts.schemaError) {
      void vscode.window.showErrorMessage(artifacts.schemaError);
    }
  };

  const refreshFromDisk = async (quietEmpty = false): Promise<void> => {
    const workspaceFolder = await selectWorkspaceFolder({ quiet: quietEmpty });
    if (!workspaceFolder) {
      return;
    }
    const settings = loadSettings();
    findingsProvider.setWorkspaceFolder(workspaceFolder);
    findingsProvider.setGroupBy(settings.groupBy);
    const runDir =
      lastArtifacts?.runDirectory && fs.existsSync(lastArtifacts.runDirectory)
        ? lastArtifacts.runDirectory
        : findLatestRunDirectory(workspaceFolder, settings.outputDirectory);
    if (!runDir) {
      clearResults();
      if (!quietEmpty) {
        void vscode.window.showInformationMessage(
          "No Engineering Assessment reports found. Run CodeStrata: Run Assessment."
        );
      }
      return;
    }
    const artifacts = loadArtifactsFromRunDirectory(runDir);
    applyArtifacts(workspaceFolder, artifacts);
  };

  const runAssessment = async (
    withAi: boolean,
    commandId: "codestrata.assess" | "codestrata.assessWithAi"
  ): Promise<void> => {
    // Slice 13.5: command ID selects AI mode — not settings alone.
    const operation: AssessmentOperation =
      commandId === "codestrata.assessWithAi"
        ? "run_assessment_with_ai"
        : "run_assessment";
    const aiRequested = commandId === "codestrata.assessWithAi" ? true : withAi;
    const folderCount = vscode.workspace.workspaceFolders?.length ?? 0;
    const session = new CommunityWorkflowSession({
      operation,
      aiRequested,
      cancellationSupported: true,
      workspaceAvailable: folderCount > 0,
      workspaceKind: classifyWorkspaceKind({ folderCount }),
      repositoryInitialized: "unknown",
    });

    if (assessmentInFlight) {
      void vscode.window.showWarningMessage(
        "A CodeStrata Engineering Assessment is already running."
      );
      session.transitionTo("validating_workspace");
      session.complete({
        status: "unavailable",
        resultCategory: "internal_workflow_error",
        primaryExit: "unavailable",
      });
      return;
    }

    try {
      session.transitionTo("validating_workspace");
      const workspaceFolder = await selectWorkspaceFolder();
      if (!workspaceFolder) {
        session.complete({
          status: "unavailable",
          resultCategory: "workspace_unavailable",
          primaryExit: "unavailable",
        });
        return;
      }
      if (!(await ensureTrusted(workspaceFolder))) {
        session.complete({
          status: "unavailable",
          resultCategory: "workspace_unsupported",
          primaryExit: "unavailable",
        });
        return;
      }
      if (!fs.existsSync(workspaceFolder)) {
        const { result: recovery } = await presentFailureRecovery({
          failureCategory: "workspace_unavailable",
          host: createVsCodeRecoveryHost({ appendOutputLine }),
        });
        session.complete({
          status: "failure",
          resultCategory: "workspace_unavailable",
          primaryExit: "failure",
          recoveryCategory: recovery.workflow_recovery_flag,
        });
        return;
      }

      // Slice 13.5 readiness: initialized repository before discovery/consent.
      const settings = loadSettings();
      const detected = detectRepositoryInitState({
        workspaceRoot: workspaceFolder,
        configuredConfigPath: settings.configPath,
      });
      const readiness = planAssessmentReadiness(detected.state);
      // Refresh session context flag without reconstructing (bounded mapping).
      void mapInitStateToWorkflowFlag(detected.state);

      if (readiness.action !== "continue_to_cli_discovery") {
        const bounded = resultForReadinessFailure(
          operation,
          aiRequested,
          readiness
        );
        const category =
          bounded.status === "repository_not_initialized"
            ? "repository_not_initialized"
            : bounded.status === "partial_repository_configuration"
              ? "partial_existing_configuration"
              : "initialization_failed";
        const { result: recovery } = await presentFailureRecovery({
          failureCategory: category,
          host: createVsCodeRecoveryHost({ appendOutputLine }),
          messageOverride: userMessageForAssessmentReadiness(bounded),
        });
        session.complete({
          status: "unavailable",
          resultCategory:
            bounded.status === "repository_not_initialized"
              ? "repository_not_initialized"
              : "initialization_failed",
          primaryExit: "unavailable",
          recoveryCategory: recovery.workflow_recovery_flag,
        });
        return;
      }

      // Compatible CLI before consent (Slice 13.2 / 13.3).
      const engine = await resolveEngine(workspaceFolder, { session });
      if (!engine) {
        const bounded = resultForCliUnavailable(operation, aiRequested);
        appendOutputLine(userMessageForAssessmentReadiness(bounded));
        const guidance = resolveRecoveryGuidance("cli_unavailable");
        session.complete({
          status: "unavailable",
          resultCategory: workflowErrorForDiscoveryStatus(
            session.getDiscoveryStatus()
          ),
          primaryExit: "unavailable",
          recoveryCategory: guidance.workflow_recovery_flag,
        });
        // Slice 13.3 owns install guidance UX; do not auto-resume assessment.
        await presentInstallationGuidance({
          discoveryStatus:
            (session.getDiscoveryStatus() as CliDiscoveryStatus) || "not_found",
          host: {
            appendOutputLine,
            refreshDiscovery: async () => {
              const again = await resolveEngine(workspaceFolder, {
                silentMissing: true,
              });
              return again?.discoveryStatus ?? (again ? "compatible" : "not_found");
            },
          },
        });
        return;
      }

      if (aiRequested) {
        const proceed = await vscode.window.showInformationMessage(
          aiOptionalGuidance(settings.aiProviderHint),
          "Continue with optional AI",
          "Cancel"
        );
        if (proceed !== "Continue with optional AI") {
          session.complete({
            status: "cancelled",
            resultCategory: "assessment_cancelled",
            primaryExit: "cancelled",
          });
          return;
        }
      }

      const extensionVersion =
        typeof context.extension?.packageJSON?.version === "string"
          ? context.extension.packageJSON.version
          : "0.2.0";

      // Slice 13.9: consent only after workspace + init + compatible CLI (+ AI confirm).
      assertConsentMayProceed({
        commandId,
        readiness: {
          workspace_ready: true,
          repository_initialized: true,
          cli_compatible: true,
          ai_confirmation_satisfied: true,
        },
      });
      session.transitionTo("awaiting_consent");
      const promptResult = await runTelemetryConsentPrompt({
        commandId,
        interactive: isTelemetryInteractive(),
        ui: createTelemetryPromptUi(),
      });
      assertFreshConsentDecision({
        priorConsentReused: promptResult.consent.priorConsentReused,
        persisted: promptResult.consent.persisted,
      });
      const integrationPolicy = createTelemetryIntegrationPolicy();
      void integrationDiagnosticsToStableDict(
        createIntegrationDiagnostics({
          operation: integrationOperationLabel(commandId),
          eligible: isTelemetryEligibleCommand(commandId),
          ordering: {
            readiness_passed: true,
            consent_allowed: true,
            blocked_stage: "none",
            reason: "ready",
          },
          consentPromptAttempted: promptResult.prompted,
          consentPromptCount: promptResult.attempts,
          consentDecisionCategory: promptResult.consent.decision,
          telemetryRuntimeCreated: true,
          telemetryTransportCategory: "unavailable",
          analyticsConstructed:
            promptResult.consent.decision === "allowed_for_session",
          analyticsSinkCategory:
            promptResult.consent.decision === "allowed_for_session"
              ? "unavailable"
              : "none",
          limitations: integrationPolicy.limitations,
        })
      );
      session.setTelemetryDecision(
        mapConsentToDecisionCategory({
          decision: promptResult.consent.decision,
          prompted: promptResult.prompted,
          interactive: isTelemetryInteractive(),
        })
      );
      const consentCategory: AssessmentConsentCategory =
        promptResult.consent.decision === "allowed_for_session"
          ? "allowed_for_session"
          : !isTelemetryInteractive()
            ? "suppressed_non_interactive"
            : "denied";
      const telemetrySession = createIsolationSession({
        consent: promptResult.consent,
        transport: defaultUnavailableTransport(),
        promptShown: promptResult.prompted,
        extensionVersion,
      });

      const args = buildAssessArgs({
        workspaceFolder,
        withAi: aiRequested,
        settings,
      });
      assertSingleAssessInvocationArgs(args);
      showOutput(true);
      appendOutputLine(`$ ${engine.executable} ${args.map(quoteIfNeeded).join(" ")}`);
      statusBar.setRunning();
      assessmentInFlight = true;
      activeAbort = new AbortController();
      const signal = activeAbort.signal;

      // Slice 13.6: one progress lifecycle starts only after readiness + consent.
      const progressLifecycle = new AssessmentProgressLifecycle({
        operation,
        aiRequested,
      });

      session.transitionTo("running_assessment");
      session.markProgressStarted();

      try {
        await runCommandWithTelemetryIsolation({
          session: telemetrySession,
          aiUsed: aiRequested,
          primary: async () => {
            session.recordCliInvocation();
            const result = await vscode.window.withProgress(
              {
                location: vscode.ProgressLocation.Notification,
                title: progressTitle(aiRequested),
                cancellable: true,
              },
              async (progress, token) => {
                progressLifecycle.start({
                  report: (value) => {
                    // Message-only — no increment/percentage (Decision A).
                    progress.report({ message: value.message });
                  },
                });
                token.onCancellationRequested(() => {
                  if (progressLifecycle.requestCancellation()) {
                    appendOutputLine(
                      "Cancellation requested — stopping Engine process…"
                    );
                    activeAbort?.abort();
                  }
                });
                const cliResult = await runCodestrataCli({
                  executable: engine.executable,
                  args,
                  cwd: workspaceFolder,
                  signal,
                  onStdout: (chunk) => appendOutput(redactSecrets(chunk)),
                  onStderr: (chunk) => appendOutput(redactSecrets(chunk)),
                });
                // Phase updates while Notification is still open (indeterminate).
                if (
                  !cliResult.cancelled &&
                  !signal.aborted &&
                  !progressLifecycle.wasCancellationRequested() &&
                  cliResult.exitCode === 0
                ) {
                  progressLifecycle.enterPhase("finalizing");
                  progressLifecycle.enterPhase("locating_report");
                }
                return cliResult;
              }
            );

            if (result.cancelled || signal.aborted || progressLifecycle.wasCancellationRequested()) {
              statusBar.setIdle();
              const { result: recovery } = await presentFailureRecovery({
                failureCategory: "assessment_cancelled",
                host: createVsCodeRecoveryHost({ appendOutputLine }),
                messageOverride:
                  "CodeStrata Engineering Assessment cancelled.",
              });
              void resultAfterEngineAssessment({
                operation,
                aiRequested,
                consent: consentCategory,
                cli: {
                  exitCode: result.exitCode,
                  cancelled: true,
                  reportAvailable: false,
                },
              });
              progressLifecycle.close(progressStatusFromPrimary("cancelled"));
              session.markProgressClosed();
              session.complete({
                status: "cancelled",
                resultCategory: "assessment_cancelled",
                primaryExit: "cancelled",
                recoveryCategory: recovery.workflow_recovery_flag,
              });
              return "cancelled" as const;
            }

            if (result.exitCode !== 0) {
              statusBar.setError(`Assessment failed (exit ${result.exitCode})`);
              const { result: recovery } = await presentFailureRecovery({
                failureCategory: "assessment_failed",
                host: createVsCodeRecoveryHost({ appendOutputLine }),
                messageOverride:
                  "CodeStrata assessment failed. See CodeStrata output.",
              });
              showOutput(false);
              void resultAfterEngineAssessment({
                operation,
                aiRequested,
                consent: consentCategory,
                cli: {
                  exitCode: result.exitCode,
                  cancelled: false,
                  reportAvailable: false,
                },
              });
              progressLifecycle.close(progressStatusFromPrimary("failure"));
              session.markProgressClosed();
              session.complete({
                status: "failure",
                resultCategory: "assessment_failed",
                primaryExit: "failure",
                recoveryCategory: recovery.workflow_recovery_flag,
              });
              return "failure" as const;
            }

            session.transitionTo("locating_report");
            const summary = parseJsonSummary(result.stdout);
            let runDirectory = summary?.run_directory
              ? path.isAbsolute(summary.run_directory)
                ? summary.run_directory
                : path.join(workspaceFolder, summary.run_directory)
              : undefined;
            if (!runDirectory || !fs.existsSync(runDirectory)) {
              runDirectory = findLatestRunDirectory(
                workspaceFolder,
                settings.outputDirectory
              );
            }

            // Report existence is a postcondition — CLI success remains primary.
            if (!runDirectory) {
              statusBar.setIdle();
              session.setReportAvailable(false);
              const bounded = resultAfterEngineAssessment({
                operation,
                aiRequested,
                consent: consentCategory,
                cli: {
                  exitCode: 0,
                  cancelled: false,
                  reportAvailable: false,
                },
              });
              const { result: recovery } = await presentFailureRecovery({
                failureCategory: "report_not_found",
                host: createVsCodeRecoveryHost({ appendOutputLine }),
              });
              progressLifecycle.close(progressStatusFromPrimary("success"));
              session.markProgressClosed();
              session.complete({
                status: "success",
                resultCategory: "report_not_found",
                primaryExit: "success",
                recoveryCategory: recovery.workflow_recovery_flag,
              });
              void bounded;
              return "success" as const;
            }

            session.setReportAvailable(true);
            const artifacts = loadArtifactsFromRunDirectory(runDirectory);
            applyArtifacts(workspaceFolder, artifacts);
            void resultAfterEngineAssessment({
              operation,
              aiRequested,
              consent: consentCategory,
              cli: {
                exitCode: 0,
                cancelled: false,
                reportAvailable: true,
              },
            });

            progressLifecycle.close(progressStatusFromPrimary("success"));
            session.markProgressClosed();

            // Slice 13.7: Approach B — prompt; do not auto-open.
            // Open failure must not rewrite assessment success.
            const open = await vscode.window.showInformationMessage(
              ASSESSMENT_COMPLETE_MESSAGE,
              ASSESSMENT_COMPLETE_OPEN_REPORT,
              ASSESSMENT_COMPLETE_DISMISS
            );
            if (open === ASSESSMENT_COMPLETE_OPEN_REPORT) {
              session.transitionTo("opening_report");
              const opened = await openHtmlReportSafe(
                workspaceFolder,
                settings.outputDirectory,
                artifacts.htmlReportPath
              );
              session.setReportOpened(opened);
              session.complete({
                status: "success",
                resultCategory: "ok",
                primaryExit: "success",
                reportOpenFailed: !opened,
              });
            } else {
              void resultForUserDeclined();
              session.complete({
                status: "success",
                resultCategory: "ok",
                primaryExit: "success",
              });
            }
            return "success" as const;
          },
        });
      } catch (error) {
        progressLifecycle.close(progressStatusFromPrimary("failure"));
        session.markProgressClosed();
        statusBar.setError("Assessment invocation failed");
        const category =
          error instanceof Error && (error as NodeJS.ErrnoException).code === "ENOENT"
            ? "cli_unavailable"
            : "cli_invocation_failed";
        const { result: recovery } = await presentFailureRecovery({
          failureCategory: category,
          host: createVsCodeRecoveryHost({ appendOutputLine }),
        });
        showOutput(false);
        session.complete({
          status: "failure",
          resultCategory: "cli_invocation_failed",
          primaryExit: "failure",
          recoveryCategory: recovery.workflow_recovery_flag,
        });
      } finally {
        if (!progressLifecycle.isClosed()) {
          progressLifecycle.close(progressStatusFromPrimary("unavailable"));
        }
        if (!session.diagnostics().progress_closed) {
          session.markProgressClosed();
        }
        assessmentInFlight = false;
        activeAbort = undefined;
        void session.diagnosticsStable();
        void progressLifecycle.diagnostics();
      }
    } catch (error) {
      if (error instanceof Error && error.name === "WorkflowTransitionError") {
        appendOutputLine(`Workflow transition error: ${error.message}`);
      }
      throw error;
    }
  };

  const onboardingDeps: OnboardingDeps = {
    context,
    resolveWorkspaceFolder: () =>
      selectWorkspaceFolder({ allowFallbackCwd: true, quiet: true }),
    resolveEngine,
    runFirstAssessment: async () => {
      await runAssessment(false, "codestrata.assess");
    },
    configureExecutable,
  };

  context.subscriptions.push(
    vscode.commands.registerCommand("codestrata.assess", async () => {
      // Slice 13.5: command selects standard assessment (--no-ai), not settings.
      await runAssessment(false, "codestrata.assess");
    }),
    vscode.commands.registerCommand("codestrata.assessWithAi", async () => {
      await runAssessment(true, "codestrata.assessWithAi");
    }),
    vscode.commands.registerCommand("codestrata.installEngine", async () => {
      const workspaceFolder =
        (await selectWorkspaceFolder({ allowFallbackCwd: true, quiet: true })) ??
        process.cwd();
      // Preserve command ID; implementation is Slice 13.3 guidance-only.
      await guidedInstallEngine(onboardingDeps, workspaceFolder, "not_attempted");
    }),
    vscode.commands.registerCommand("codestrata.showWelcome", async () => {
      await runWelcomeFlow(onboardingDeps, { markCompleteOnSuccess: true });
    }),
    vscode.commands.registerCommand("codestrata.checkEnvironment", async () => {
      const folders = vscode.workspace.workspaceFolders;
      const workspaceFolder =
        folders && folders.length > 0
          ? await selectWorkspaceFolder()
          : process.cwd();
      if (!workspaceFolder) {
        return;
      }
      showOutput(true);
      const engine = await resolveEngine(workspaceFolder);
      if (!engine) {
        return;
      }
      const settings = loadSettings();
      const versionText =
        engine.versionOutput?.replace(/^CodeStrata\s+/, "") ?? "";
      const compatibility = evaluateCliCompatibility({
        cliVersion: versionText || undefined,
      });
      // Reuse discovery compatibility — do not probe again for matrix decision.
      appendOutputLine(
        `CodeStrata environment check (${engine.source}). Compatibility: ${doctorCompatibilityLabel(
          compatibility.verdict
        )}.`
      );
      void vscode.window.showInformationMessage(
        `CodeStrata CLI: ${doctorCompatibilityLabel(compatibility.verdict)}`
      );
      const doctor = await runCodestrataCli({
        executable: engine.executable,
        args: buildDoctorArgs(settings),
        cwd: workspaceFolder,
        onStdout: (chunk) => appendOutput(redactSecrets(chunk)),
        onStderr: (chunk) => appendOutput(redactSecrets(chunk)),
      });
      void vscode.window.showInformationMessage(
        doctor.exitCode === 0
          ? `CodeStrata environment OK (${doctorCompatibilityLabel(
              compatibility.verdict
            )}). See output.`
          : `CodeStrata doctor exited ${doctor.exitCode}. See output.`
      );
    }),
    vscode.commands.registerCommand("codestrata.openHtmlReport", async () => {
      // Slice 13.7: open existing local HTML only — never rerun assessment/init/CLI.
      const folderCount = vscode.workspace.workspaceFolders?.length ?? 0;
      const session = new CommunityWorkflowSession({
        operation: "open_report",
        aiRequested: false,
        cancellationSupported: false,
        workspaceAvailable: folderCount > 0,
        workspaceKind: classifyWorkspaceKind({ folderCount }),
      });
      session.transitionTo("validating_workspace");
      const workspaceFolder = await selectWorkspaceFolder();
      if (!workspaceFolder) {
        session.complete({
          status: "unavailable",
          resultCategory: "workspace_unavailable",
          primaryExit: "unavailable",
        });
        return;
      }
      const settings = loadSettings();
      const located = locateHtmlReport({
        workspaceRoot: workspaceFolder,
        outputDirectory: settings.outputDirectory,
        sessionHtmlPath: lastArtifacts?.htmlReportPath,
      });
      if (located.status !== "available" || !located.htmlPath) {
        const category =
          located.status === "unsafe_path"
            ? "report_path_unsafe"
            : "report_not_found";
        const { result: recovery } = await presentFailureRecovery({
          failureCategory: category,
          host: createVsCodeRecoveryHost({ appendOutputLine }),
        });
        session.setReportAvailable(false);
        session.complete({
          status: "failure",
          resultCategory: "report_not_found",
          primaryExit: "failure",
          recoveryCategory: recovery.workflow_recovery_flag,
        });
        return;
      }
      session.setReportAvailable(true);
      if (
        located.runDirectory &&
        lastArtifacts?.runDirectory !== located.runDirectory
      ) {
        lastArtifacts = loadArtifactsFromRunDirectory(located.runDirectory);
      }
      session.transitionTo("opening_report");
      const opened = await openHtmlReportSafe(
        workspaceFolder,
        settings.outputDirectory,
        located.htmlPath
      );
      session.setReportOpened(opened);
      session.complete({
        status: opened ? "success" : "failure",
        resultCategory: opened ? "ok" : "report_open_failed",
        primaryExit: opened ? "success" : "failure",
        reportOpenFailed: !opened,
      });
    }),
    vscode.commands.registerCommand("codestrata.refreshFindings", async () => {
      await refreshFromDisk();
    }),
    vscode.commands.registerCommand("codestrata.refreshRecommendations", async () => {
      await refreshFromDisk();
      await vscode.commands.executeCommand("codestrata.recommendations.focus");
    }),
    vscode.commands.registerCommand("codestrata.showRecommendations", async () => {
      await vscode.commands.executeCommand("codestrata.recommendations.focus");
      if (!lastArtifacts?.recommendations.length) {
        await refreshFromDisk();
      }
    }),
    vscode.commands.registerCommand("codestrata.clearResults", async () => {
      clearResults();
      void vscode.window.showInformationMessage("CodeStrata results cleared.");
    }),
    vscode.commands.registerCommand("codestrata.openOutput", async () => {
      showOutput(false);
    }),
    vscode.commands.registerCommand("codestrata.openDocumentation", async () => {
      await vscode.env.openExternal(vscode.Uri.parse(ENGINE_DOCS_QUICK_START));
    }),
    vscode.commands.registerCommand("codestrata.init", async () => {
      const folderCount = vscode.workspace.workspaceFolders?.length ?? 0;
      const session = new CommunityWorkflowSession({
        operation: "initialize_repository",
        aiRequested: false,
        cancellationSupported: false,
        workspaceAvailable: folderCount > 0,
        workspaceKind: classifyWorkspaceKind({ folderCount }),
        repositoryInitialized: "unknown",
      });
      session.transitionTo("validating_workspace");
      const workspaceFolder = await selectWorkspaceFolder();
      if (!workspaceFolder || !(await ensureTrusted(workspaceFolder))) {
        const category = workspaceFolder
          ? "workspace_unsupported"
          : "workspace_unavailable";
        const { result: recovery } = await presentFailureRecovery({
          failureCategory: category,
          host: createVsCodeRecoveryHost({ appendOutputLine }),
          messageOverride: userMessageForInitResult(
            createRepoInitResult({
              status: "workspace_unavailable",
              prior_state: "unknown",
              final_state: "unknown",
              engine_invocation_count: 0,
              config_created: false,
              existing_configuration_preserved: true,
              post_init_verified: false,
              recovery_category: "select_workspace",
            })
          ),
        });
        session.complete({
          status: "unavailable",
          resultCategory: category,
          primaryExit: "unavailable",
          recoveryCategory: recovery.workflow_recovery_flag,
        });
        return;
      }

      // Compatible CLI required before init (Slice 13.2 / 13.3).
      const engine = await resolveEngine(workspaceFolder, { session });
      if (!engine) {
        session.complete({
          status: "unavailable",
          resultCategory: workflowErrorForDiscoveryStatus(
            session.getDiscoveryStatus()
          ),
          primaryExit: "unavailable",
        });
        await presentInstallationGuidance({
          discoveryStatus:
            (session.getDiscoveryStatus() as CliDiscoveryStatus) || "not_found",
          host: {
            appendOutputLine,
            refreshDiscovery: async () => {
              const again = await resolveEngine(workspaceFolder, {
                silentMissing: true,
              });
              return again?.discoveryStatus ?? (again ? "compatible" : "not_found");
            },
          },
        });
        // Do not auto-resume init after guidance.
        return;
      }

      const settings = loadSettings();
      const detected = detectRepositoryInitState({
        workspaceRoot: workspaceFolder,
        configuredConfigPath: settings.configPath,
      });
      const plan = planRepositoryInitialization(detected.state);

      if (plan.action !== "invoke_engine_init") {
        const bounded = resultForPlanWithoutCli(plan);
        const message = userMessageForInitResult(bounded);
        appendOutputLine(message);
        if (bounded.status === "already_initialized") {
          void vscode.window.showInformationMessage(message);
        } else {
          void vscode.window.showErrorMessage(message);
        }
        session.complete({
          status:
            bounded.status === "already_initialized" ? "success" : "failure",
          resultCategory:
            bounded.status === "already_initialized"
              ? "ok"
              : "initialization_failed",
          primaryExit:
            bounded.status === "already_initialized" ? "success" : "failure",
        });
        return;
      }

      const args = buildInitArgs(settings);
      assertInitArgsForbidForce(args);
      showOutput(true);
      appendOutputLine("Initializing CodeStrata repository configuration (Engine CLI)…");
      session.transitionTo("initializing");
      session.recordCliInvocation();
      const result = await runCodestrataCli({
        executable: engine.executable,
        args,
        cwd: workspaceFolder,
        onStdout: (chunk) => appendOutput(redactSecrets(chunk)),
        onStderr: (chunk) => appendOutput(redactSecrets(chunk)),
      });

      const after = detectRepositoryInitState({
        workspaceRoot: workspaceFolder,
        configuredConfigPath: settings.configPath,
      });
      const bounded = resultAfterEngineInit({
        priorState: plan.prior_state,
        cli: { exitCode: result.exitCode, cancelled: result.cancelled },
        finalState: after.state,
      });
      const message = userMessageForInitResult(bounded);
      appendOutputLine(message);
      if (bounded.status === "initialized") {
        void vscode.window.showInformationMessage(message);
      } else if (bounded.status === "cancelled") {
        void vscode.window.showWarningMessage(message);
      } else {
        void vscode.window.showErrorMessage(message);
      }
      session.complete({
        status:
          bounded.status === "initialized"
            ? "success"
            : bounded.status === "cancelled"
              ? "cancelled"
              : "failure",
        resultCategory:
          bounded.status === "initialized"
            ? "ok"
            : bounded.status === "cancelled"
              ? "assessment_cancelled"
              : "initialization_failed",
        primaryExit:
          bounded.status === "initialized"
            ? "success"
            : bounded.status === "cancelled"
              ? "cancelled"
              : "failure",
      });
    }),
    vscode.commands.registerCommand("codestrata.doctor", async () => {
      await vscode.commands.executeCommand("codestrata.checkEnvironment");
    }),
    vscode.commands.registerCommand("codestrata.setFindingsGroupBy", async () => {
      const picked = await vscode.window.showQuickPick(
        [
          { label: "Severity", value: "severity" },
          { label: "Domain", value: "domain" },
          { label: "File", value: "file" },
          { label: "Rule", value: "rule" },
        ],
        { title: "Group CodeStrata findings by" }
      );
      if (!picked) {
        return;
      }
      const groupBy = picked.value as FindingsGroupBy;
      await vscode.workspace
        .getConfiguration()
        .update("codestrata.findings.groupBy", groupBy, vscode.ConfigurationTarget.Workspace);
      findingsProvider.setGroupBy(groupBy);
    }),
    vscode.commands.registerCommand("codestrata.filterFindings", async () => {
      const value = await vscode.window.showInputBox({
        title: "Filter CodeStrata findings",
        prompt: "Search title, rule, severity, domain, or file (empty clears)",
        value: "",
      });
      if (value === undefined) {
        return;
      }
      findingsProvider.setFilter(value);
    }),
    vscode.commands.registerCommand(
      "codestrata.openFindingLocation",
      async (finding?: Finding) => {
        const workspaceFolder = await selectWorkspaceFolder();
        if (!workspaceFolder || !finding) {
          return;
        }
        const relative = primaryEvidencePath(finding);
        if (!relative) {
          void vscode.window.showInformationMessage(
            `${finding.title} — no source file path in evidence (rule: ${
              finding.rule_id ?? "n/a"
            }).`
          );
          return;
        }
        const resolved = resolveWorkspaceRelativePath(workspaceFolder, relative);
        if (!resolved) {
          return;
        }
        if (!resolved.insideWorkspace) {
          const proceed = await vscode.window.showWarningMessage(
            `Evidence path is outside the workspace:\n${resolved.path}`,
            "Open Anyway",
            "Cancel"
          );
          if (proceed !== "Open Anyway") {
            return;
          }
        }
        if (!fs.existsSync(resolved.path)) {
          void vscode.window.showWarningMessage(
            `File not found (moved or deleted): ${relative}`
          );
          return;
        }
        const doc = await vscode.workspace.openTextDocument(resolved.path);
        const editor = await vscode.window.showTextDocument(doc, { preview: true });
        const line = extractEvidenceLine(primaryEvidenceExcerpt(finding)) ?? 1;
        const lineIndex = Math.max(0, line - 1);
        const position = new vscode.Position(lineIndex, 0);
        editor.selection = new vscode.Selection(position, position);
        editor.revealRange(
          new vscode.Range(position, position),
          vscode.TextEditorRevealType.InCenter
        );
      }
    ),
    vscode.workspace.onDidChangeWorkspaceFolders(() => {
      clearResults();
      void refreshFromDisk(true);
    })
  );

  appendOutputLine(
    `CodeStrata – Engineering Intelligence activated (Community). Supported report schema: ${SUPPORTED_SCHEMA_DOC}.`
  );
  void refreshFromDisk(true);
  void maybeRunFirstRun(onboardingDeps);
}

export function deactivate(): void {
  activeAbort?.abort();
  activeAbort = undefined;
  assessmentInFlight = false;
  lastArtifacts = undefined;
}

async function openHtmlReportSafe(
  workspaceRoot: string,
  outputDirectory: string,
  htmlPath: string | undefined
): Promise<boolean> {
  const adapter: OpenHtmlAdapter = {
    async openLocalFile(absolutePath) {
      const uri = vscode.Uri.file(absolutePath);
      return vscode.env.openExternal(uri);
    },
  };
  const result = await openValidatedHtmlReport({
    workspaceRoot,
    outputDirectory,
    htmlPath,
    open: adapter,
    reportExpected: true,
  });
  if (!result.open_succeeded) {
    void presentFailureRecovery({
      failureCategory: "report_open_failed",
      host: createVsCodeRecoveryHost({ appendOutputLine }),
      messageOverride: userMessageForReportResult(result),
    });
  }
  return result.open_succeeded;
}

function quoteIfNeeded(token: string): string {
  return /\s/.test(token) ? `"${token}"` : token;
}
