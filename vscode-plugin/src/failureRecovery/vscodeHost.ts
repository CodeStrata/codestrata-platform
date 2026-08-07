/** VS Code host adapter for Slice 13.8 recovery presentation. */

import * as vscode from "vscode";

import type { RecoveryNotificationHost } from "./presentation";

export function createVsCodeRecoveryHost(options?: {
  readonly appendOutputLine?: (line: string) => void;
}): RecoveryNotificationHost {
  return {
    showErrorMessage: (message, ...actions) =>
      vscode.window.showErrorMessage(message, ...actions),
    showWarningMessage: (message, ...actions) =>
      vscode.window.showWarningMessage(message, ...actions),
    showInformationMessage: (message, ...actions) =>
      vscode.window.showInformationMessage(message, ...actions),
    executeCommand: (commandId) =>
      vscode.commands.executeCommand(commandId),
    appendOutputLine: options?.appendOutputLine,
  };
}
