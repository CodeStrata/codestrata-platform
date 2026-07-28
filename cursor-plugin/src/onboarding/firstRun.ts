/**
 * First-run Community onboarding for CodeStrata Cursor Extension.
 */

import * as vscode from "vscode";

import {
  ENGINE_DOCS_QUICK_START,
} from "../engine/cliContract";
import {
  MIN_ENGINE_VERSION,
  parseEngineVersionOutput,
  SUPPORTED_ENGINE_VERSION_RANGE,
  SUPPORTED_REPORT_SCHEMA,
} from "../engine/compatibility";
import type { EngineCandidate } from "../engine/discovery";
import { appendOutputLine, showOutput } from "../ui/output";

export { classifyEnginePresence } from "./state";
export const STATE_FIRST_RUN_DONE = "codestrata.cursor.firstRunCompleted";
export const STATE_WELCOME_DISMISSED = "codestrata.cursor.welcomeDismissed";

export interface CursorOnboardingDeps {
  context: vscode.ExtensionContext;
  resolveWorkspaceFolder: () => Promise<string | undefined>;
  resolveEngine: (
    workspaceFolder: string,
    options?: { silentMissing?: boolean }
  ) => Promise<(EngineCandidate & { versionOutput?: string; version?: string }) | undefined>;
  runFirstAssessment: () => Promise<void>;
  showSuggestedQuestions: () => Promise<void>;
  installEngine: () => Promise<void>;
  checkEnvironment: () => Promise<void>;
  configureExecutable: () => Promise<void>;
}

export async function maybeRunFirstRun(deps: CursorOnboardingDeps): Promise<void> {
  if (deps.context.globalState.get(STATE_FIRST_RUN_DONE) === true) {
    return;
  }
  await runWelcomeFlow(deps, { markCompleteOnSuccess: true });
}

export async function runWelcomeFlow(
  deps: CursorOnboardingDeps,
  options?: { markCompleteOnSuccess?: boolean }
): Promise<void> {
  const workspaceFolder =
    (await deps.resolveWorkspaceFolder()) ??
    vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ??
    process.cwd();

  showOutput(true);
  appendOutputLine("CodeStrata Cursor Extension — first-run / welcome…");
  appendOutputLine(
    `Supported Engine ${SUPPORTED_ENGINE_VERSION_RANGE}; report schema ${SUPPORTED_REPORT_SCHEMA}.`
  );

  const existing = await deps.resolveEngine(workspaceFolder, { silentMissing: true });
  if (existing) {
    const versionInfo = parseEngineVersionOutput(existing.versionOutput ?? "");
    if (!versionInfo.compatible) {
      const action = await vscode.window.showWarningMessage(
        `CodeStrata Engine ${versionInfo.version ?? "unknown"} is outside ${SUPPORTED_ENGINE_VERSION_RANGE} ` +
          `(need ${MIN_ENGINE_VERSION}+).`,
        "Update Engine",
        "Configure Different Executable",
        "Open Compatibility Guide",
        "Continue Anyway"
      );
      if (action === "Update Engine") {
        await deps.installEngine();
        return;
      }
      if (action === "Configure Different Executable") {
        await deps.configureExecutable();
        return;
      }
      if (action === "Open Compatibility Guide") {
        await vscode.env.openExternal(vscode.Uri.parse(ENGINE_DOCS_QUICK_START));
        return;
      }
    } else {
      const next = await vscode.window.showInformationMessage(
        "Welcome to CodeStrata Cursor Extension (Community Edition).\n\n" +
          "CodeStrata Engine is ready. Run an Engineering Assessment to ground Cursor Chat / Agent " +
          "with Engineering Intelligence — the extension does not analyze source code independently.",
        "Run Engineering Assessment",
        "View Suggested Questions",
        "Open Documentation",
        "Dismiss"
      );
      if (next === "Run Engineering Assessment") {
        await deps.runFirstAssessment();
      } else if (next === "View Suggested Questions") {
        await deps.showSuggestedQuestions();
      } else if (next === "Open Documentation") {
        await vscode.env.openExternal(vscode.Uri.parse(ENGINE_DOCS_QUICK_START));
      }
      if (options?.markCompleteOnSuccess) {
        await deps.context.globalState.update(STATE_FIRST_RUN_DONE, true);
      }
      return;
    }
  }

  const choice = await vscode.window.showInformationMessage(
    "Welcome to CodeStrata\n\n" +
      "CodeStrata Engine is required to generate repository Engineering Intelligence " +
      "for Cursor Chat / Agent.",
    { modal: true },
    "Install CodeStrata Engine",
    "Configure Engine Executable",
    "Check Environment",
    "Open Installation Guide",
    "Open Output"
  );

  if (choice === "Install CodeStrata Engine") {
    await deps.installEngine();
    if (options?.markCompleteOnSuccess) {
      const after = await deps.resolveEngine(workspaceFolder, { silentMissing: true });
      if (after) {
        await deps.context.globalState.update(STATE_FIRST_RUN_DONE, true);
      }
    }
    return;
  }
  if (choice === "Configure Engine Executable") {
    await deps.configureExecutable();
    return;
  }
  if (choice === "Check Environment") {
    await deps.checkEnvironment();
    return;
  }
  if (choice === "Open Installation Guide") {
    await vscode.env.openExternal(vscode.Uri.parse(ENGINE_DOCS_QUICK_START));
    return;
  }
  if (choice === "Open Output") {
    showOutput(false);
    return;
  }
  await deps.context.globalState.update(STATE_WELCOME_DISMISSED, true);
}
