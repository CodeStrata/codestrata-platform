/**
 * VS Code adapters for Slice 13.3 installation guidance (Approach A).
 */

import * as vscode from "vscode";

import type { CliDiscoveryStatus } from "../cliDiscovery/results";
import {
  detectInstallationPlatform,
  runInstallationGuidance,
  type InstallationGuidanceResult,
  type InstallationUiAdapters,
} from "./index";

export type InstallationGuidanceHost = {
  readonly refreshDiscovery: () => Promise<CliDiscoveryStatus>;
  readonly appendOutputLine: (line: string) => void;
};

function createAdapters(host: InstallationGuidanceHost): InstallationUiAdapters {
  return {
    async showActions(message, actions) {
      const choice = await vscode.window.showInformationMessage(
        message,
        { modal: false },
        ...actions
      );
      return choice;
    },
    async showQuickPick(items, title) {
      const picked = await vscode.window.showQuickPick(
        items.map((item) => ({
          label: item.label,
          description: item.description,
          id: item.id,
        })),
        { title, ignoreFocusOut: true }
      );
      return picked?.id;
    },
    async copyText(text) {
      try {
        await vscode.env.clipboard.writeText(text);
        return true;
      } catch {
        return false;
      }
    },
    async openTerminal() {
      try {
        const terminal = vscode.window.createTerminal({
          name: "CodeStrata CLI Install",
        });
        terminal.show(true);
        // Do not sendText — Approach A does not auto-execute.
        return true;
      } catch {
        return false;
      }
    },
    async openExternalUrl(url) {
      try {
        await vscode.env.openExternal(vscode.Uri.parse(url));
        return true;
      } catch {
        return false;
      }
    },
    async openExecutableSettings() {
      await vscode.commands.executeCommand(
        "workbench.action.openSettings",
        "codestrata.engine.executable"
      );
    },
    refreshDiscovery: host.refreshDiscovery,
    appendOutputLine: host.appendOutputLine,
  };
}

/**
 * Authoritative entry for codestrata.installEngine and discovery-failure guidance.
 * Never runs package managers, downloads binaries, or mutates PATH/settings.
 */
export async function presentInstallationGuidance(options: {
  readonly discoveryStatus: CliDiscoveryStatus | "not_attempted";
  readonly host: InstallationGuidanceHost;
}): Promise<InstallationGuidanceResult> {
  return runInstallationGuidance({
    discoveryStatus: options.discoveryStatus,
    platform: detectInstallationPlatform(),
    adapters: createAdapters(options.host),
  });
}
