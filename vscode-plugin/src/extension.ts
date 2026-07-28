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
  buildVersionArgs,
  ENGINE_DOCS_QUICK_START,
  ENGINE_INSTALL_HINT,
  parseJsonSummary,
} from "./engine/cliContract";
import { runCodestrataCli } from "./engine/cliRunner";
import { parseEngineVersionOutput } from "./engine/compatibility";
import {
  formatCandidateLabel,
  listEngineCandidates,
  redactSecrets,
  type EngineCandidate,
} from "./engine/discovery";
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
import { StatusBarController } from "./ui/statusBar";
import { FindingsTreeProvider } from "./views/findingsTree";
import { RecommendationsTreeProvider } from "./views/recommendationsTree";
import { extractEvidenceLine, resolveWorkspaceRelativePath } from "./workspace/paths";

export type ResolvedEngine = EngineCandidate & { versionOutput?: string };

let lastArtifacts: ParsedAssessmentArtifacts | undefined;
let assessmentInFlight = false;
let activeAbort: AbortController | undefined;

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
    options?: { silentMissing?: boolean }
  ): Promise<ResolvedEngine | undefined> => {
    const settings = loadSettings();
    const folders =
      vscode.workspace.workspaceFolders?.map((folder) => folder.uri.fsPath) ?? [
        workspaceFolder,
      ];
    const candidates = listEngineCandidates(settings.executable, folders);
    appendOutputLine("Resolving CodeStrata Engine executable…");
    for (const candidate of candidates) {
      appendOutputLine(`  candidate: ${formatCandidateLabel(candidate)}`);
    }

    for (const candidate of candidates) {
      try {
        const probe = await runCodestrataCli({
          executable: candidate.executable,
          args: buildVersionArgs(),
          cwd: workspaceFolder,
        });
        if (probe.exitCode === 0) {
          const versionInfo = parseEngineVersionOutput(probe.stdout);
          appendOutputLine(
            `Using Engine: ${formatCandidateLabel(candidate)} — ${redactSecrets(
              probe.stdout.trim().split(/\r?\n/)[0] || "version ok"
            )}`
          );
          if (versionInfo.version) {
            appendOutputLine(
              `Version compatibility: ${
                versionInfo.compatible ? "OK" : "WARN"
              } (${versionInfo.version})`
            );
          }
          return { ...candidate, versionOutput: probe.stdout };
        }
      } catch (error) {
        const err = error as NodeJS.ErrnoException;
        if (err.code !== "ENOENT") {
          appendOutputLine(
            `  probe failed for ${candidate.executable}: ${redactSecrets(String(error))}`
          );
        }
      }
    }

    if (options?.silentMissing) {
      appendOutputLine("Engine not found (silent for onboarding).");
      return undefined;
    }

    const action = await vscode.window.showErrorMessage(
      "CodeStrata Engine CLI was not found. This Community extension requires CodeStrata Engine.",
      "Install Engine",
      "Open Installation Docs",
      "Configure Executable",
      "Show Output"
    );
    if (action === "Install Engine") {
      await vscode.commands.executeCommand("codestrata.installEngine");
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
          "No Engineering Assessment reports found. Run CodeStrata: Run Engineering Assessment."
        );
      }
      return;
    }
    const artifacts = loadArtifactsFromRunDirectory(runDir);
    applyArtifacts(workspaceFolder, artifacts);
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
    if (!(await ensureTrusted(workspaceFolder))) {
      return;
    }
    if (!fs.existsSync(workspaceFolder)) {
      void vscode.window.showErrorMessage("Workspace folder does not exist.");
      return;
    }

    const engine = await resolveEngine(workspaceFolder);
    if (!engine) {
      return;
    }

    const settings = loadSettings();
    if (withAi) {
      const proceed = await vscode.window.showInformationMessage(
        aiOptionalGuidance(settings.aiProviderHint),
        "Continue with optional AI",
        "Cancel"
      );
      if (proceed !== "Continue with optional AI") {
        return;
      }
    }

    const args = buildAssessArgs({
      workspaceFolder,
      withAi,
      settings,
    });
    showOutput(true);
    appendOutputLine(`$ ${engine.executable} ${args.map(quoteIfNeeded).join(" ")}`);
    statusBar.setRunning();
    assessmentInFlight = true;
    activeAbort = new AbortController();
    const signal = activeAbort.signal;

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
            appendOutputLine("Cancellation requested — stopping Engine process…");
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
        statusBar.setIdle();
        void vscode.window.showInformationMessage(
          "CodeStrata Engineering Assessment cancelled."
        );
        appendOutputLine("Assessment cancelled by user (not treated as failure).");
        return;
      }

      if (result.exitCode !== 0) {
        statusBar.setError(`Assessment failed (exit ${result.exitCode})`);
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
        statusBar.setError("Assessment finished but no report directory found");
        void vscode.window.showWarningMessage(
          "Assessment finished but no report directory was found. Try Refresh Findings or rerun."
        );
        return;
      }

      const artifacts = loadArtifactsFromRunDirectory(runDirectory);
      applyArtifacts(workspaceFolder, artifacts);

      const aiNote =
        withAi && summary?.ai_status
          ? ` AI status: ${summary.ai_status}.`
          : withAi
            ? " AI is optional; check output if enhancements were skipped."
            : " Deterministic mode (--no-ai).";

      const open = await vscode.window.showInformationMessage(
        `Engineering Assessment complete: ${artifacts.findings.length} findings, ` +
          `${artifacts.recommendations.length} recommendations.` +
          aiNote,
        "Open HTML Report",
        "Show Findings"
      );
      if (open === "Open HTML Report") {
        await openHtmlReportSafe(artifacts.htmlReportPath);
      }
      if (open === "Show Findings") {
        await vscode.commands.executeCommand("codestrata.findings.focus");
      }
    } catch (error) {
      statusBar.setError(String(error));
      const message =
        error instanceof Error && (error as NodeJS.ErrnoException).code === "ENOENT"
          ? `CodeStrata Engine CLI not found (${engine.executable}). ${ENGINE_INSTALL_HINT}`
          : `CodeStrata assessment failed: ${redactSecrets(String(error))}`;
      void vscode.window.showErrorMessage(message);
      appendOutputLine(message);
      showOutput(false);
    } finally {
      assessmentInFlight = false;
      activeAbort = undefined;
    }
  };

  const onboardingDeps: OnboardingDeps = {
    context,
    resolveWorkspaceFolder: () =>
      selectWorkspaceFolder({ allowFallbackCwd: true, quiet: true }),
    resolveEngine,
    runFirstAssessment: async () => {
      await runAssessment(false);
    },
    configureExecutable,
  };

  context.subscriptions.push(
    vscode.commands.registerCommand("codestrata.assess", async () => {
      const settings = loadSettings();
      await runAssessment(!settings.defaultNoAi);
    }),
    vscode.commands.registerCommand("codestrata.assessWithAi", async () => {
      await runAssessment(true);
    }),
    vscode.commands.registerCommand("codestrata.installEngine", async () => {
      const workspaceFolder =
        (await selectWorkspaceFolder({ allowFallbackCwd: true, quiet: true })) ??
        process.cwd();
      await guidedInstallEngine(onboardingDeps, workspaceFolder);
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
      const doctor = await runCodestrataCli({
        executable: engine.executable,
        args: buildDoctorArgs(settings),
        cwd: workspaceFolder,
        onStdout: (chunk) => appendOutput(redactSecrets(chunk)),
        onStderr: (chunk) => appendOutput(redactSecrets(chunk)),
      });
      void vscode.window.showInformationMessage(
        doctor.exitCode === 0
          ? `CodeStrata environment OK (${formatCandidateLabel(engine)}). See output.`
          : `CodeStrata doctor exited ${doctor.exitCode}. See output.`
      );
    }),
    vscode.commands.registerCommand("codestrata.openHtmlReport", async () => {
      const workspaceFolder = await selectWorkspaceFolder();
      if (!workspaceFolder) {
        return;
      }
      const settings = loadSettings();
      const runDir =
        lastArtifacts?.htmlReportPath && fs.existsSync(lastArtifacts.htmlReportPath)
          ? lastArtifacts.runDirectory
          : findLatestRunDirectory(workspaceFolder, settings.outputDirectory);
      if (!runDir) {
        void vscode.window.showWarningMessage(
          "No HTML Engineering Assessment report found. Run an assessment first."
        );
        return;
      }
      const artifacts =
        lastArtifacts?.runDirectory === runDir
          ? lastArtifacts
          : loadArtifactsFromRunDirectory(runDir);
      await openHtmlReportSafe(artifacts.htmlReportPath);
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
      const workspaceFolder = await selectWorkspaceFolder();
      if (!workspaceFolder || !(await ensureTrusted(workspaceFolder))) {
        return;
      }
      const engine = await resolveEngine(workspaceFolder);
      if (!engine) {
        return;
      }
      const settings = loadSettings();
      showOutput(true);
      const result = await runCodestrataCli({
        executable: engine.executable,
        args: buildInitArgs(settings),
        cwd: workspaceFolder,
        onStdout: (chunk) => appendOutput(redactSecrets(chunk)),
        onStderr: (chunk) => appendOutput(redactSecrets(chunk)),
      });
      void vscode.window.showInformationMessage(
        result.exitCode === 0
          ? "CodeStrata configuration initialized."
          : `CodeStrata init exited ${result.exitCode}. See output.`
      );
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
    `CodeStrata VS Code Extension activated (Community). Supported report schema: ${SUPPORTED_SCHEMA_DOC}.`
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

async function openHtmlReportSafe(htmlPath: string | undefined): Promise<void> {
  if (!htmlPath || !fs.existsSync(htmlPath)) {
    void vscode.window.showWarningMessage(
      "Engineering Assessment report.html not found. Run an assessment or refresh findings."
    );
    return;
  }
  const uri = vscode.Uri.file(htmlPath);
  await vscode.env.openExternal(uri);
}

function quoteIfNeeded(token: string): string {
  return /\s/.test(token) ? `"${token}"` : token;
}
