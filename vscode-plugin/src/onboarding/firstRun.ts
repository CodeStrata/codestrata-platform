/**
 * First-run Community onboarding for CodeStrata – Engineering Intelligence.
 *
 * Slice 13.2: activation must not probe until Get Started.
 * Slice 13.3: installation is guidance-only (no automatic package-manager run).
 */

import * as vscode from "vscode";

import { presentInstallationGuidance } from "../cliInstallation/vscodeHost";
import type { CliDiscoveryStatus } from "../cliDiscovery/results";
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
import { appendOutput, appendOutputLine, showOutput } from "../ui/output";
import {
  FIRST_RUN_ACTION_DISMISS,
  FIRST_RUN_ACTION_DONE,
  FIRST_RUN_ACTION_ENABLE_AI,
  FIRST_RUN_ACTION_GET_STARTED,
  FIRST_RUN_ACTION_LATER,
  FIRST_RUN_ACTION_RUN_FIRST,
  FIRST_RUN_CLI_MISSING_MESSAGE,
  FIRST_RUN_ENGINE_READY_MESSAGE,
  FIRST_RUN_WELCOME_MESSAGE,
} from "../ui/presentationCopy";
import { offerOptionalAiSetup, openEngineDocs } from "./aiSetup";

export const STATE_FIRST_RUN_DONE = "codestrata.firstRunCompleted";
export const STATE_WELCOME_DISMISSED = "codestrata.welcomeDismissed";

export interface OnboardingDeps {
  context: vscode.ExtensionContext;
  resolveWorkspaceFolder: () => Promise<string | undefined>;
  resolveEngine: (
    workspaceFolder: string,
    options?: { silentMissing?: boolean }
  ) => Promise<
    | (EngineCandidate & {
        versionOutput?: string;
        discoveryStatus?: CliDiscoveryStatus;
      })
    | undefined
  >;
  runFirstAssessment: () => Promise<void>;
  configureExecutable: (executable: string) => Promise<void>;
}

/**
 * Activation-safe entry (Slice 13.2): do not probe/spawn the CLI until the user
 * explicitly chooses Get Started. Discovery remains lazy and local-only.
 */
export async function maybeRunFirstRun(deps: OnboardingDeps): Promise<void> {
  if (deps.context.globalState.get(STATE_FIRST_RUN_DONE) === true) {
    return;
  }
  if (deps.context.globalState.get(STATE_WELCOME_DISMISSED) === true) {
    return;
  }
  const choice = await vscode.window.showInformationMessage(
    FIRST_RUN_WELCOME_MESSAGE,
    FIRST_RUN_ACTION_GET_STARTED,
    FIRST_RUN_ACTION_LATER
  );
  if (choice !== FIRST_RUN_ACTION_GET_STARTED) {
    await deps.context.globalState.update(STATE_WELCOME_DISMISSED, true);
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
        "Installation Guidance…",
        "Continue Anyway",
        "Learn More"
      );
      if (action === "Installation Guidance…") {
        await guidedInstallEngine(deps, workspaceFolder, "incompatible");
        return;
      }
      if (action === "Learn More") {
        await openEngineDocs();
        return;
      }
    } else {
      appendOutputLine(
        `Engine ready: ${existing.source} (${versionInfo.version ?? "ok"})`
      );
      await runDoctorQuiet(existing.executable, workspaceFolder);
      const next = await vscode.window.showInformationMessage(
        FIRST_RUN_ENGINE_READY_MESSAGE,
        FIRST_RUN_ACTION_RUN_FIRST,
        FIRST_RUN_ACTION_ENABLE_AI,
        FIRST_RUN_ACTION_DISMISS
      );
      if (next === FIRST_RUN_ACTION_RUN_FIRST) {
        await deps.runFirstAssessment();
      } else if (next === FIRST_RUN_ACTION_ENABLE_AI) {
        await offerOptionalAiSetup();
      }
      if (options?.markCompleteOnSuccess) {
        await deps.context.globalState.update(STATE_FIRST_RUN_DONE, true);
      }
      return;
    }
  }

  const choice = await vscode.window.showInformationMessage(
    FIRST_RUN_CLI_MISSING_MESSAGE,
    { modal: true },
    "Installation Guidance…",
    "Learn More",
    "Later"
  );

  if (choice === "Learn More") {
    await openEngineDocs();
    return;
  }
  if (choice !== "Installation Guidance…") {
    await deps.context.globalState.update(STATE_WELCOME_DISMISSED, true);
    return;
  }

  const ready = await guidedInstallEngine(deps, workspaceFolder, "not_found");
  if (!ready) {
    return;
  }

  if (options?.markCompleteOnSuccess) {
    await deps.context.globalState.update(STATE_FIRST_RUN_DONE, true);
  }

  const after = await vscode.window.showInformationMessage(
    "If you installed CodeStrata CLI, you can run an assessment now.",
    FIRST_RUN_ACTION_RUN_FIRST,
    FIRST_RUN_ACTION_ENABLE_AI,
    FIRST_RUN_ACTION_DONE
  );
  if (after === FIRST_RUN_ACTION_RUN_FIRST) {
    await deps.runFirstAssessment();
  } else if (after === FIRST_RUN_ACTION_ENABLE_AI) {
    await offerOptionalAiSetup();
  }
}

/**
 * Compatibility entry for codestrata.installEngine / welcome.
 * Slice 13.3: guidance-only — never runs package managers or mutates PATH.
 */
export async function guidedInstallEngine(
  deps: OnboardingDeps,
  workspaceFolder: string,
  discoveryStatus: CliDiscoveryStatus | "not_attempted" = "not_attempted"
): Promise<boolean> {
  showOutput(true);
  const result = await presentInstallationGuidance({
    discoveryStatus,
    host: {
      appendOutputLine,
      refreshDiscovery: async () => {
        const again = await deps.resolveEngine(workspaceFolder, {
          silentMissing: true,
        });
        if (again?.discoveryStatus) {
          return again.discoveryStatus;
        }
        return again ? "compatible" : "not_found";
      },
    },
  });

  if (result.status === "not_required" || result.status === "rediscovery_succeeded") {
    return true;
  }

  // After guidance, do not auto-resume product commands.
  const again = await deps.resolveEngine(workspaceFolder, { silentMissing: true });
  return Boolean(again);
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
