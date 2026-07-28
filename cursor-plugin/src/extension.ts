import * as fs from "node:fs";
import * as path from "node:path";

import * as vscode from "vscode";

import { readSettingsFromWorkspaceConfig } from "./config/settings";
import { buildConversationContext, type ConversationContext } from "./conversation/context";
import {
  clearCursorConversationRule,
  writeCursorConversationRule,
} from "./conversation/cursorRules";
import {
  constructPrompt,
} from "./conversation/prompts";
import type { SuggestedQuestion } from "./conversation/suggestedQuestions";
import {
  buildAssessArgs,
  buildDoctorArgs,
  buildVersionArgs,
  ENGINE_DOCS_QUICK_START,
  ENGINE_INSTALL_HINT,
  parseJsonSummary,
} from "./engine/cliContract";
import { runCodestrataCli } from "./engine/cliRunner";
import {
  parseEngineVersionOutput,
  SUPPORTED_ENGINE_VERSION_RANGE,
} from "./engine/compatibility";
import {
  formatCandidateLabel,
  listEngineCandidates,
  redactSecrets,
  type EngineCandidate,
} from "./engine/discovery";
import {
  ENGINE_DOCS_TROUBLESHOOTING,
  installEngine,
  selectInstallMethods,
} from "./engine/installer";
import {
  maybeRunFirstRun,
  runWelcomeFlow,
  type CursorOnboardingDeps,
} from "./onboarding/firstRun";
import {
  findLatestRunDirectory,
  loadArtifactsFromRunDirectory,
} from "./reports/parser";
import { SUPPORTED_SCHEMA_DOC } from "./reports/schema";
import type { ParsedAssessmentArtifacts } from "./reports/types";
import {
  appendOutput,
  appendOutputLine,
  disposeOutputChannel,
  showOutput,
} from "./ui/output";
import { StatusBarController } from "./ui/statusBar";
import { AssessmentStatusProvider } from "./views/statusTree";
import { SuggestedQuestionsProvider } from "./views/suggestedTree";

type ResolvedEngine = EngineCandidate & {
  versionOutput?: string;
  version?: string;
};

let lastArtifacts: ParsedAssessmentArtifacts | undefined;
let lastContext: ConversationContext | undefined;
let lastWorkspaceFolder: string | undefined;
let lastEngineVersion: string | undefined;
let assessmentInFlight = false;
let activeAbort: AbortController | undefined;

export function activate(context: vscode.ExtensionContext): void {
  const statusBar = new StatusBarController();
  const suggestedProvider = new SuggestedQuestionsProvider();
  const statusProvider = new AssessmentStatusProvider();

  context.subscriptions.push(
    statusBar,
    vscode.window.registerTreeDataProvider(
      "codestrata.suggestedQuestions",
      suggestedProvider
    ),
    vscode.window.registerTreeDataProvider("codestrata.assessmentStatus", statusProvider),
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

  const selectWorkspaceFolder = async (options?: {
    allowMissing?: boolean;
  }): Promise<string | undefined> => {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders || folders.length === 0) {
      if (!options?.allowMissing) {
        void vscode.window.showErrorMessage(
          "CodeStrata requires an open workspace folder (local repository)."
        );
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
        placeHolder: "Multi-root workspace — choose one repository root",
        ignoreFocusOut: true,
      }
    );
    return picked?.folder.uri.fsPath;
  };

  const ensureTrusted = async (): Promise<boolean> => {
    if (vscode.workspace.isTrusted) {
      return true;
    }
    const choice = await vscode.window.showWarningMessage(
      "This workspace is untrusted. CodeStrata will not run Engine or write .cursor/rules until the workspace is trusted.",
      "Manage Workspace Trust",
      "Cancel"
    );
    if (choice === "Manage Workspace Trust") {
      await vscode.commands.executeCommand("workbench.trust.manage");
    }
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
    options?: { silentMissing?: boolean }
  ): Promise<ResolvedEngine | undefined> => {
    const settings = loadSettings();
    const folders =
      vscode.workspace.workspaceFolders?.map((folder) => folder.uri.fsPath) ?? [
        workspaceFolder,
      ];
    const candidates = listEngineCandidates(settings.executable, folders);
    appendOutputLine("Engine discovery candidates:");
    for (const candidate of candidates) {
      appendOutputLine(`  ${formatCandidateLabel(candidate)}`);
    }

    for (const candidate of candidates) {
      try {
        const probe = await runCodestrataCli({
          executable: candidate.executable,
          args: buildVersionArgs(),
          cwd: workspaceFolder,
        });
        if (probe.exitCode !== 0) {
          continue;
        }
        const versionInfo = parseEngineVersionOutput(probe.stdout);
        appendOutputLine(
          `Selected: ${formatCandidateLabel(candidate)} — ${redactSecrets(
            probe.stdout.trim().split(/\r?\n/)[0] || "ok"
          )}`
        );
        appendOutputLine(
          `Compatibility (${SUPPORTED_ENGINE_VERSION_RANGE}): ${
            versionInfo.compatible ? "OK" : "FAIL"
          }${versionInfo.version ? ` (${versionInfo.version})` : ""}`
        );
        if (!versionInfo.compatible) {
          statusBar.setState(
            "engine-incompatible",
            versionInfo.reason ?? "incompatible Engine"
          );
          statusProvider.setState(
            "engine-incompatible",
            versionInfo.reason ?? "incompatible Engine"
          );
          if (!options?.silentMissing) {
            const action = await vscode.window.showWarningMessage(
              versionInfo.reason ?? "CodeStrata Engine version is incompatible.",
              "Install / Update Engine",
              "Continue Anyway",
              "Documentation"
            );
            if (action === "Install / Update Engine") {
              await vscode.commands.executeCommand("codestrata.installEngine");
              return undefined;
            }
            if (action === "Documentation") {
              await vscode.env.openExternal(vscode.Uri.parse(ENGINE_DOCS_QUICK_START));
              return undefined;
            }
          }
        } else {
          statusBar.setState("ready");
        }
        return {
          ...candidate,
          versionOutput: probe.stdout,
          version: versionInfo.version,
        };
      } catch (error) {
        const err = error as NodeJS.ErrnoException;
        if (err.code !== "ENOENT") {
          appendOutputLine(
            `  probe failed for ${candidate.executable}: ${redactSecrets(String(error))}`
          );
        }
      }
    }

    statusBar.setState("engine-missing");
    statusProvider.setState("engine-missing");
    if (options?.silentMissing) {
      return undefined;
    }
    const action = await vscode.window.showErrorMessage(
      "CodeStrata Engine CLI was not found. This Community Cursor extension requires CodeStrata Engine.",
      "Install Engine",
      "Configure Executable",
      "Check Environment",
      "Open Documentation",
      "Show Output"
    );
    if (action === "Install Engine") {
      await vscode.commands.executeCommand("codestrata.installEngine");
    } else if (action === "Configure Executable") {
      await vscode.commands.executeCommand(
        "workbench.action.openSettings",
        "codestrata.engine.executable"
      );
    } else if (action === "Check Environment") {
      await vscode.commands.executeCommand("codestrata.checkEnvironment");
    } else if (action === "Open Documentation") {
      await vscode.env.openExternal(vscode.Uri.parse(ENGINE_DOCS_QUICK_START));
    } else if (action === "Show Output") {
      showOutput(false);
    }
    appendOutputLine(ENGINE_INSTALL_HINT);
    return undefined;
  };

  const clearLocalState = (options?: {
    removeRule?: boolean;
    workspaceFolder?: string;
  }): void => {
    lastArtifacts = undefined;
    lastContext = undefined;
    suggestedProvider.setHasAssessment(false);
    statusBar.setState("no-assessment");
    statusProvider.setState("no-assessment");
    if (options?.removeRule && options.workspaceFolder) {
      const result = clearCursorConversationRule(options.workspaceFolder);
      if (result.skippedForeign) {
        appendOutputLine(
          "Left non-CodeStrata Cursor rule untouched (will not delete user rules)."
        );
      }
    }
  };

  const applyConversationContext = (
    workspaceFolder: string,
    artifacts: ParsedAssessmentArtifacts,
    engineVersion?: string
  ): ConversationContext | undefined => {
    if (artifacts.schemaError) {
      clearLocalState({ removeRule: true, workspaceFolder });
      void vscode.window.showErrorMessage(artifacts.schemaError);
      statusBar.setState("failed", artifacts.schemaError);
      return undefined;
    }
    const repoLabel = path.basename(workspaceFolder);
    const conversation = buildConversationContext(artifacts, {
      workspaceFolder,
      repositoryLabel: repoLabel,
      engineVersion: engineVersion ?? lastEngineVersion,
    });
    lastArtifacts = artifacts;
    lastContext = conversation;
    lastWorkspaceFolder = workspaceFolder;
    const writeResult = writeCursorConversationRule(workspaceFolder, conversation);
    suggestedProvider.setHasAssessment(true);
    statusBar.setReady(conversation.findingCount);
    statusProvider.setFromContext(conversation, repoLabel);
    appendOutputLine(
      writeResult.wrote
        ? `Conversation context written → ${writeResult.path}`
        : `Conversation context unchanged (fingerprint match) → ${writeResult.path}`
    );
    for (const warning of artifacts.parseWarnings) {
      appendOutputLine(`Warning: ${warning}`);
    }
    return conversation;
  };

  const missingAssessmentHelp = async (): Promise<void> => {
    const action = await vscode.window.showInformationMessage(
      "No valid CodeStrata Engineering Assessment is loaded. Run an assessment before asking grounded questions.",
      "Run Engineering Assessment",
      "Check Environment",
      "Open Documentation",
      "Open Output"
    );
    if (action === "Run Engineering Assessment") {
      await vscode.commands.executeCommand("codestrata.assess");
    } else if (action === "Check Environment") {
      await vscode.commands.executeCommand("codestrata.checkEnvironment");
    } else if (action === "Open Documentation") {
      await vscode.env.openExternal(vscode.Uri.parse(ENGINE_DOCS_QUICK_START));
    } else if (action === "Open Output") {
      showOutput(false);
    }
  };

  const refreshFromDisk = async (quietEmpty = false): Promise<void> => {
    const workspaceFolder = await selectWorkspaceFolder({ allowMissing: quietEmpty });
    if (!workspaceFolder) {
      return;
    }
    const settings = loadSettings();
    const runDir =
      lastWorkspaceFolder === workspaceFolder &&
      lastArtifacts?.runDirectory &&
      fs.existsSync(lastArtifacts.runDirectory)
        ? lastArtifacts.runDirectory
        : findLatestRunDirectory(workspaceFolder, settings.outputDirectory);
    if (!runDir) {
      clearLocalState({ removeRule: true, workspaceFolder });
      if (!quietEmpty) {
        await missingAssessmentHelp();
      }
      return;
    }
    const artifacts = loadArtifactsFromRunDirectory(runDir);
    const applied = applyConversationContext(
      workspaceFolder,
      artifacts,
      lastEngineVersion
    );
    if (!applied) {
      return;
    }
    if (!quietEmpty) {
      void vscode.window.showInformationMessage(
        `Assessment context loaded: ${artifacts.findings.length} findings, ` +
          `${artifacts.recommendations.length} recommendations. Cursor rule refreshed.`
      );
    }
  };

  const runAssessment = async (withAi: boolean): Promise<void> => {
    if (assessmentInFlight) {
      void vscode.window.showWarningMessage(
        "A CodeStrata Engineering Assessment is already running."
      );
      return;
    }
    const workspaceFolder = await selectWorkspaceFolder();
    if (!workspaceFolder) {
      return;
    }
    if (!(await ensureTrusted())) {
      return;
    }
    const engine = await resolveEngine(workspaceFolder);
    if (!engine) {
      return;
    }
    lastEngineVersion = engine.version;
    const settings = loadSettings();
    if (withAi) {
      const proceed = await vscode.window.showInformationMessage(
        "Optional AI uses your CodeStrata Engine provider configuration " +
          "(Bedrock / OpenAI / Azure OpenAI / Anthropic). Credentials stay in Engine — never in this extension.",
        "Continue with optional AI",
        "Cancel"
      );
      if (proceed !== "Continue with optional AI") {
        return;
      }
    }

    const args = buildAssessArgs({ workspaceFolder, withAi, settings });
    showOutput(true);
    appendOutputLine(`$ ${engine.executable} ${args.map(quoteIfNeeded).join(" ")}`);
    statusBar.setRunning();
    statusProvider.setState("running");
    assessmentInFlight = true;
    activeAbort = new AbortController();
    const signal = activeAbort.signal;
    const previousContext = lastContext;
    const previousArtifacts = lastArtifacts;

    try {
      const result = await vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: withAi
            ? "CodeStrata Engineering Assessment (optional AI)…"
            : "CodeStrata Engineering Assessment…",
          cancellable: true,
        },
        async (_progress, token) => {
          token.onCancellationRequested(() => {
            appendOutputLine("Cancellation requested — stopping Engine…");
            activeAbort?.abort();
          });
          return runCodestrataCli({
            executable: engine.executable,
            args,
            cwd: workspaceFolder,
            signal,
            onStdout: (chunk) => appendOutput(redactSecrets(chunk)),
            onStderr: (chunk) => appendOutput(redactSecrets(chunk)),
          });
        }
      );

      if (result.cancelled || signal.aborted) {
        // Do not create partial conversation context; keep previous valid context.
        lastContext = previousContext;
        lastArtifacts = previousArtifacts;
        if (previousContext) {
          statusBar.setReady(previousContext.findingCount);
          statusProvider.setFromContext(
            previousContext,
            path.basename(workspaceFolder)
          );
          suggestedProvider.setHasAssessment(true);
        } else {
          statusBar.setState("cancelled");
          statusProvider.setState("cancelled");
          suggestedProvider.setHasAssessment(false);
        }
        void vscode.window.showInformationMessage(
          "CodeStrata Engineering Assessment cancelled (not treated as failure)."
        );
        appendOutputLine("Assessment cancelled by user.");
        return;
      }

      if (result.exitCode !== 0) {
        statusBar.setError(`Assessment failed (exit ${result.exitCode})`);
        statusProvider.setState("failed", `exit ${result.exitCode}`);
        void vscode.window.showErrorMessage(
          `CodeStrata assessment failed (exit ${result.exitCode}). See CodeStrata output.`
        );
        showOutput(false);
        return;
      }

      const summary = parseJsonSummary(result.stdout);
      let runDirectory = summary?.run_directory
        ? path.isAbsolute(summary.run_directory)
          ? summary.run_directory
          : path.join(workspaceFolder, summary.run_directory)
        : undefined;
      if (!runDirectory || !fs.existsSync(runDirectory)) {
        runDirectory = findLatestRunDirectory(workspaceFolder, settings.outputDirectory);
      }
      if (!runDirectory) {
        statusBar.setError("No report directory found");
        statusProvider.setState("failed", "no report directory");
        void vscode.window.showWarningMessage(
          "Assessment finished but no report directory was found."
        );
        return;
      }

      const artifacts = loadArtifactsFromRunDirectory(runDirectory);
      const applied = applyConversationContext(
        workspaceFolder,
        artifacts,
        engine.version
      );
      if (!applied) {
        return;
      }

      const open = await vscode.window.showInformationMessage(
        `Engineering Assessment complete: ${artifacts.findings.length} findings, ` +
          `${artifacts.recommendations.length} recommendations. ` +
          `Cursor context updated (.cursor/rules/codestrata-engineering.mdc). ` +
          (artifacts.htmlReportPath ? "HTML report available." : "HTML report not found."),
        "Open Report",
        "Show Suggested Questions",
        "Copy Grounded Prompt"
      );
      if (open === "Open Report") {
        await openHtmlReportSafe(artifacts.htmlReportPath);
      } else if (open === "Show Suggested Questions") {
        await vscode.commands.executeCommand("codestrata.suggestedQuestions.focus");
      } else if (open === "Copy Grounded Prompt") {
        await vscode.commands.executeCommand("codestrata.copyConversationPrompt");
      }
    } catch (error) {
      statusBar.setError(String(error));
      statusProvider.setState("failed", redactSecrets(String(error)));
      void vscode.window.showErrorMessage(
        `CodeStrata assessment failed: ${redactSecrets(String(error))}`
      );
    } finally {
      assessmentInFlight = false;
      activeAbort = undefined;
    }
  };

  const askWithPrompt = async (question: string): Promise<void> => {
    if (!lastContext) {
      await missingAssessmentHelp();
      return;
    }
    const constructed = constructPrompt(lastContext, question);
    await vscode.env.clipboard.writeText(constructed.fullPrompt);
    const action = await vscode.window.showInformationMessage(
      "Grounded CodeStrata prompt copied. Paste into Cursor Chat or Agent. " +
        "Context also applies via .cursor/rules/codestrata-engineering.mdc when Cursor loads project rules.",
      "Open Cursor Chat",
      "Dismiss"
    );
    if (action === "Open Cursor Chat") {
      for (const command of [
        "aichat.newchataction",
        "workbench.action.chat.open",
        "composer.openComposer",
      ]) {
        try {
          await vscode.commands.executeCommand(command);
          break;
        } catch {
          // best-effort only — Cursor command IDs vary
        }
      }
    }
  };

  const guidedInstall = async (): Promise<void> => {
    const workspaceFolder =
      (await selectWorkspaceFolder({ allowMissing: true })) ?? process.cwd();
    if (!(await ensureTrusted())) {
      return;
    }
    const methods = selectInstallMethods();
    if (methods.length === 0) {
      void vscode.window.showErrorMessage(
        "No supported installer found (uv, pipx, or Python pip). Install Python 3.12+ then retry.",
        "Open Documentation"
      );
      return;
    }
    const preferred = await vscode.window.showQuickPick(
      methods.map((method) => ({
        label: method.label,
        description: `${method.executable} ${method.args.join(" ")}`,
        method,
      })),
      {
        title: "Install CodeStrata Engine",
        placeHolder: "Official mechanisms: uv tool / pipx / pip --user",
        ignoreFocusOut: true,
      }
    );
    if (!preferred) {
      return;
    }
    showOutput(true);
    appendOutputLine(
      `Installing via: ${preferred.method.executable} ${preferred.method.args.join(" ")}`
    );
    const result = await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: "Installing CodeStrata Engine…",
        cancellable: false,
      },
      async () =>
        installEngine({
          preferredMethodId: preferred.method.id,
          onStdout: (chunk) => appendOutput(redactSecrets(chunk)),
          onStderr: (chunk) => appendOutput(redactSecrets(chunk)),
        })
    );
    if (!result.ok) {
      const action = await vscode.window.showErrorMessage(
        result.reason ?? "Engine installation failed.",
        "Retry",
        "Open Troubleshooting",
        "Configure Executable"
      );
      if (action === "Retry") {
        await guidedInstall();
      } else if (action === "Open Troubleshooting") {
        await vscode.env.openExternal(vscode.Uri.parse(ENGINE_DOCS_TROUBLESHOOTING));
      } else if (action === "Configure Executable") {
        await vscode.commands.executeCommand(
          "workbench.action.openSettings",
          "codestrata.engine.executable"
        );
      }
      return;
    }
    if (result.resolvedExecutable && result.resolvedExecutable !== "codestrata") {
      await configureExecutable(result.resolvedExecutable);
    }
    const engine = await resolveEngine(workspaceFolder);
    if (!engine) {
      return;
    }
    const doctor = await runCodestrataCli({
      executable: engine.executable,
      args: buildDoctorArgs(loadSettings()),
      cwd: workspaceFolder,
      onStdout: (chunk) => appendOutput(redactSecrets(chunk)),
      onStderr: (chunk) => appendOutput(redactSecrets(chunk)),
    });
    void vscode.window.showInformationMessage(
      doctor.exitCode === 0
        ? `CodeStrata Engine ready (${formatCandidateLabel(engine)}).`
        : `Engine installed; doctor exited ${doctor.exitCode}. See output.`
    );
  };

  context.subscriptions.push(
    vscode.commands.registerCommand("codestrata.assess", async () => {
      const settings = loadSettings();
      await runAssessment(!settings.defaultNoAi);
    }),
    vscode.commands.registerCommand("codestrata.assessWithAi", async () => {
      await runAssessment(true);
    }),
    vscode.commands.registerCommand("codestrata.refreshAssessment", async () => {
      await refreshFromDisk(false);
    }),
    vscode.commands.registerCommand("codestrata.clearAssessment", async () => {
      const workspaceFolder =
        lastWorkspaceFolder ?? (await selectWorkspaceFolder({ allowMissing: true }));
      clearLocalState({
        removeRule: true,
        workspaceFolder: workspaceFolder,
      });
      lastWorkspaceFolder = undefined;
      void vscode.window.showInformationMessage(
        "CodeStrata assessment context cleared. CodeStrata-managed Cursor rule removed (user rules preserved)."
      );
    }),
    vscode.commands.registerCommand("codestrata.installEngine", async () => {
      await guidedInstall();
    }),
    vscode.commands.registerCommand("codestrata.checkEnvironment", async () => {
      const workspaceFolder =
        (await selectWorkspaceFolder({ allowMissing: true })) ?? process.cwd();
      showOutput(true);
      const engine = await resolveEngine(workspaceFolder);
      if (!engine) {
        return;
      }
      const doctor = await runCodestrataCli({
        executable: engine.executable,
        args: buildDoctorArgs(loadSettings()),
        cwd: workspaceFolder,
        onStdout: (chunk) => appendOutput(redactSecrets(chunk)),
        onStderr: (chunk) => appendOutput(redactSecrets(chunk)),
      });
      void vscode.window.showInformationMessage(
        doctor.exitCode === 0
          ? `CodeStrata environment OK (${formatCandidateLabel(engine)}).`
          : `codestrata doctor exited ${doctor.exitCode}. See output.`
      );
    }),
    vscode.commands.registerCommand("codestrata.missingAssessmentHelp", async () => {
      await missingAssessmentHelp();
    }),
    vscode.commands.registerCommand("codestrata.openHtmlReport", async () => {
      const workspaceFolder = await selectWorkspaceFolder();
      if (!workspaceFolder) {
        return;
      }
      const settings = loadSettings();
      const runDir =
        lastWorkspaceFolder === workspaceFolder &&
        lastArtifacts?.runDirectory &&
        fs.existsSync(lastArtifacts.runDirectory)
          ? lastArtifacts.runDirectory
          : findLatestRunDirectory(workspaceFolder, settings.outputDirectory);
      if (!runDir) {
        await missingAssessmentHelp();
        return;
      }
      const artifacts =
        lastArtifacts?.runDirectory === runDir
          ? lastArtifacts
          : loadArtifactsFromRunDirectory(runDir);
      await openHtmlReportSafe(artifacts.htmlReportPath);
    }),
    vscode.commands.registerCommand("codestrata.showFindings", async () => {
      if (!lastContext) {
        await missingAssessmentHelp();
        return;
      }
      showOutput(true);
      appendOutputLine("Findings (public assessment artifacts):");
      for (const finding of lastContext.findings.slice(0, 20)) {
        appendOutputLine(
          `[${finding.severity}] ${finding.title}${finding.rule_id ? ` (${finding.rule_id})` : ""}`
        );
      }
      void vscode.window.showInformationMessage(
        `${lastContext.findingCount} findings — see CodeStrata output.`
      );
    }),
    vscode.commands.registerCommand("codestrata.showRecommendations", async () => {
      if (!lastContext) {
        await missingAssessmentHelp();
        return;
      }
      showOutput(true);
      appendOutputLine("Recommendations (public assessment artifacts):");
      for (const rec of lastContext.recommendations.slice(0, 20)) {
        appendOutputLine(
          `${rec.title}${rec.priority ? ` [${rec.priority}]` : ""}`
        );
      }
      void vscode.window.showInformationMessage(
        `${lastContext.recommendationCount} recommendations — see CodeStrata output.`
      );
    }),
    vscode.commands.registerCommand("codestrata.copyConversationPrompt", async () => {
      await askWithPrompt(
        "What are the highest-priority engineering risks in this repository according to the CodeStrata Engineering Assessment?"
      );
    }),
    vscode.commands.registerCommand(
      "codestrata.askSuggested",
      async (question?: SuggestedQuestion) => {
        if (!question) {
          return;
        }
        if (!lastContext && question.requiresAssessment) {
          await missingAssessmentHelp();
          return;
        }
        await askWithPrompt(question.prompt);
      }
    ),
    vscode.commands.registerCommand("codestrata.openOutput", async () => {
      showOutput(false);
    }),
    vscode.commands.registerCommand("codestrata.openDocumentation", async () => {
      await vscode.env.openExternal(vscode.Uri.parse(ENGINE_DOCS_QUICK_START));
    }),
    vscode.commands.registerCommand("codestrata.showWelcome", async () => {
      await runWelcomeFlow(onboardingDeps, { markCompleteOnSuccess: true });
    }),
    vscode.workspace.onDidChangeWorkspaceFolders(() => {
      clearLocalState({
        removeRule: false,
        workspaceFolder: lastWorkspaceFolder,
      });
      lastWorkspaceFolder = undefined;
      void refreshFromDisk(true);
    })
  );

  const onboardingDeps: CursorOnboardingDeps = {
    context,
    resolveWorkspaceFolder: async () =>
      selectWorkspaceFolder({ allowMissing: true }),
    resolveEngine,
    runFirstAssessment: async () => {
      await runAssessment(false);
    },
    showSuggestedQuestions: async () => {
      await vscode.commands.executeCommand("codestrata.suggestedQuestions.focus");
    },
    installEngine: async () => {
      await guidedInstall();
    },
    checkEnvironment: async () => {
      await vscode.commands.executeCommand("codestrata.checkEnvironment");
    },
    configureExecutable: async () => {
      await vscode.commands.executeCommand(
        "workbench.action.openSettings",
        "codestrata.engine.executable"
      );
    },
  };

  appendOutputLine(
    `CodeStrata Cursor Extension activated (Community). Report schema ${SUPPORTED_SCHEMA_DOC}.`
  );
  if (!vscode.workspace.workspaceFolders?.length) {
    statusBar.setState("no-assessment", "No folder open");
    statusProvider.setState("no-assessment", "No folder open");
  } else {
    void refreshFromDisk(true);
  }
  void maybeRunFirstRun(onboardingDeps);
}

export function deactivate(): void {
  activeAbort?.abort();
  activeAbort = undefined;
  assessmentInFlight = false;
  lastArtifacts = undefined;
  lastContext = undefined;
  lastWorkspaceFolder = undefined;
}

async function openHtmlReportSafe(htmlPath: string | undefined): Promise<void> {
  if (!htmlPath || !fs.existsSync(htmlPath)) {
    void vscode.window.showWarningMessage(
      "Engineering Assessment report.html not found. Run an assessment first."
    );
    return;
  }
  await vscode.env.openExternal(vscode.Uri.file(htmlPath));
}

function quoteIfNeeded(token: string): string {
  return /\s/.test(token) ? `"${token}"` : token;
}
