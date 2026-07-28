/**
 * First-run Community onboarding for CodeStrata VS Code Extension.
 */

import * as vscode from "vscode";

import { DEFAULT_SETTINGS } from "../config/settings";
import {
  buildDoctorArgs,
  buildVersionArgs,
  ENGINE_DOCS_QUICK_START,
} from "../engine/cliContract";
import { runCodestrataCli } from "../engine/cliRunner";
import {
  MIN_ENGINE_VERSION,
  parseEngineVersionOutput,
  SUPPORTED_ENGINE_VERSION_RANGE,
  SUPPORTED_REPORT_SCHEMA,
} from "../engine/compatibility";
import {
  formatCandidateLabel,
  listEngineCandidates,
  redactSecrets,
  type EngineCandidate,
} from "../engine/discovery";
import {
  ENGINE_DOCS_TROUBLESHOOTING,
  installEngine,
  selectInstallMethods,
} from "../engine/installer";
import { appendOutput, appendOutputLine, showOutput } from "../ui/output";
import { offerOptionalAiSetup, openEngineDocs } from "./aiSetup";

export const STATE_FIRST_RUN_DONE = "codestrata.firstRunCompleted";
export const STATE_WELCOME_DISMISSED = "codestrata.welcomeDismissed";

export interface OnboardingDeps {
  context: vscode.ExtensionContext;
  resolveWorkspaceFolder: () => Promise<string | undefined>;
  resolveEngine: (
    workspaceFolder: string,
    options?: { silentMissing?: boolean }
  ) => Promise<(EngineCandidate & { versionOutput?: string }) | undefined>;
  runFirstAssessment: () => Promise<void>;
  configureExecutable: (executable: string) => Promise<void>;
}

export async function maybeRunFirstRun(deps: OnboardingDeps): Promise<void> {
  if (deps.context.globalState.get(STATE_FIRST_RUN_DONE) === true) {
    return;
  }
  await runWelcomeFlow(deps, { markCompleteOnSuccess: true });
}

export async function runWelcomeFlow(
  deps: OnboardingDeps,
  options?: { markCompleteOnSuccess?: boolean }
): Promise<void> {
  const workspaceFolder =
    (await deps.resolveWorkspaceFolder()) ??
    vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ??
    process.cwd();

  showOutput(true);
  appendOutputLine("CodeStrata first-run / welcome…");
  appendOutputLine(
    `Supported Engine ${SUPPORTED_ENGINE_VERSION_RANGE}; report schema ${SUPPORTED_REPORT_SCHEMA}.`
  );

  const existing = await deps.resolveEngine(workspaceFolder, { silentMissing: true });
  if (existing) {
    const versionInfo = parseEngineVersionOutput(existing.versionOutput ?? "");
    if (!versionInfo.compatible) {
      const action = await vscode.window.showWarningMessage(
        versionInfo.reason ??
          `CodeStrata Engine ${versionInfo.version ?? "unknown"} may be incompatible (need ${MIN_ENGINE_VERSION}+).`,
        "Install / Update Engine",
        "Continue Anyway",
        "Learn More"
      );
      if (action === "Install / Update Engine") {
        await guidedInstallEngine(deps, workspaceFolder);
        return;
      }
      if (action === "Learn More") {
        await openEngineDocs();
        return;
      }
    } else {
      appendOutputLine(
        `Engine ready: ${formatCandidateLabel(existing)} (${versionInfo.version})`
      );
      await runDoctorQuiet(existing.executable, workspaceFolder);
      const next = await vscode.window.showInformationMessage(
        "Welcome to CodeStrata. CodeStrata Engine is ready. Engineering Intelligence for Modern Software Organizations.",
        "Run First Engineering Assessment",
        "Enable AI Enhancements…",
        "Dismiss"
      );
      if (next === "Run First Engineering Assessment") {
        await deps.runFirstAssessment();
      } else if (next === "Enable AI Enhancements…") {
        await offerOptionalAiSetup();
      }
      if (options?.markCompleteOnSuccess) {
        await deps.context.globalState.update(STATE_FIRST_RUN_DONE, true);
      }
      return;
    }
  }

  const choice = await vscode.window.showInformationMessage(
    "Welcome to CodeStrata\n\nEngineering Intelligence for Modern Software Organizations.\n\nTo begin, CodeStrata Engine needs to be installed.",
    { modal: true },
    "Install Engine",
    "Learn More",
    "Later"
  );

  if (choice === "Learn More") {
    await openEngineDocs();
    return;
  }
  if (choice !== "Install Engine") {
    await deps.context.globalState.update(STATE_WELCOME_DISMISSED, true);
    return;
  }

  const installed = await guidedInstallEngine(deps, workspaceFolder);
  if (!installed) {
    return;
  }

  if (options?.markCompleteOnSuccess) {
    await deps.context.globalState.update(STATE_FIRST_RUN_DONE, true);
  }

  const after = await vscode.window.showInformationMessage(
    "CodeStrata Engine installed successfully.",
    "Run First Engineering Assessment",
    "Enable AI Enhancements…",
    "Done"
  );
  if (after === "Run First Engineering Assessment") {
    await deps.runFirstAssessment();
  } else if (after === "Enable AI Enhancements…") {
    await offerOptionalAiSetup();
  }
}

export async function guidedInstallEngine(
  deps: OnboardingDeps,
  workspaceFolder: string
): Promise<boolean> {
  const methods = selectInstallMethods();
  if (methods.length === 0) {
    const action = await vscode.window.showErrorMessage(
      "Cannot install CodeStrata Engine automatically: Python 3.12+, uv, or pipx was not found.",
      "Open Quick Start",
      "Configure Executable",
      "Retry"
    );
    if (action === "Open Quick Start") {
      await openEngineDocs();
    } else if (action === "Configure Executable") {
      await vscode.commands.executeCommand(
        "workbench.action.openSettings",
        "codestrata.engine.executable"
      );
    } else if (action === "Retry") {
      return guidedInstallEngine(deps, workspaceFolder);
    }
    return false;
  }

  const preferred = await vscode.window.showQuickPick(
    methods.map((method) => ({
      label: method.label,
      description: method.id,
      method,
    })),
    {
      title: "Install CodeStrata Engine",
      placeHolder: "Choose an installation method (official: pip / uv / pipx)",
      ignoreFocusOut: true,
    }
  );
  if (!preferred) {
    return false;
  }

  showOutput(true);
  appendOutputLine(
    `Installing CodeStrata Engine via ${preferred.method.executable} ${preferred.method.args.join(" ")}…`
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
    appendOutputLine(`Install failed: ${result.reason ?? "unknown"}`);
    for (const tip of result.troubleshooting ?? []) {
      appendOutputLine(`  • ${tip}`);
    }
    const action = await vscode.window.showErrorMessage(
      result.reason ?? "CodeStrata Engine installation failed.",
      "Retry",
      "Open Troubleshooting",
      "Configure Executable",
      "Show Output"
    );
    if (action === "Retry") {
      return guidedInstallEngine(deps, workspaceFolder);
    }
    if (action === "Open Troubleshooting") {
      await vscode.env.openExternal(vscode.Uri.parse(ENGINE_DOCS_TROUBLESHOOTING));
    } else if (action === "Configure Executable") {
      await vscode.commands.executeCommand(
        "workbench.action.openSettings",
        "codestrata.engine.executable"
      );
    } else if (action === "Show Output") {
      showOutput(false);
    }
    return false;
  }

  if (result.resolvedExecutable && result.resolvedExecutable !== "codestrata") {
    await deps.configureExecutable(result.resolvedExecutable);
    appendOutputLine(`Configured codestrata.engine.executable = ${result.resolvedExecutable}`);
  }

  const engine = await deps.resolveEngine(workspaceFolder, { silentMissing: true });
  if (!engine) {
    void vscode.window.showWarningMessage(
      "Install finished but codestrata version could not be verified. Configure the executable path.",
      "Configure Executable"
    );
    return false;
  }

  const versionInfo = parseEngineVersionOutput(engine.versionOutput ?? "");
  appendOutputLine(
    `Verified: ${formatCandidateLabel(engine)} — ${versionInfo.version ?? "ok"}`
  );
  await runDoctorQuiet(engine.executable, workspaceFolder);
  void vscode.window.showInformationMessage(
    `CodeStrata Engine ${versionInfo.version ?? ""} ready (${formatCandidateLabel(engine)}).`
  );
  return true;
}

async function runDoctorQuiet(executable: string, cwd: string): Promise<void> {
  try {
    const doctor = await runCodestrataCli({
      executable,
      args: buildDoctorArgs(DEFAULT_SETTINGS),
      cwd,
      onStdout: (chunk) => appendOutput(redactSecrets(chunk)),
      onStderr: (chunk) => appendOutput(redactSecrets(chunk)),
    });
    appendOutputLine(
      doctor.exitCode === 0
        ? "codestrata doctor: OK"
        : `codestrata doctor exited ${doctor.exitCode} (see output).`
    );
  } catch (error) {
    appendOutputLine(`codestrata doctor skipped: ${redactSecrets(String(error))}`);
  }
}

export async function probeEngineVersion(
  candidate: EngineCandidate,
  cwd: string
): Promise<{ ok: boolean; versionOutput: string }> {
  try {
    const probe = await runCodestrataCli({
      executable: candidate.executable,
      args: buildVersionArgs(),
      cwd,
    });
    return { ok: probe.exitCode === 0, versionOutput: probe.stdout };
  } catch {
    return { ok: false, versionOutput: "" };
  }
}

export function logDiscoveryCandidates(
  configured: string,
  workspaceFolders: string[]
): void {
  const candidates = listEngineCandidates(configured, workspaceFolders);
  appendOutputLine("Engine discovery candidates:");
  for (const candidate of candidates) {
    appendOutputLine(`  ${formatCandidateLabel(candidate)}`);
  }
}

export { ENGINE_DOCS_QUICK_START };
