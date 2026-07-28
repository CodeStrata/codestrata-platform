import * as vscode from "vscode";

let channel: vscode.OutputChannel | undefined;

export function getOutputChannel(): vscode.OutputChannel {
  if (!channel) {
    channel = vscode.window.createOutputChannel("CodeStrata");
  }
  return channel;
}

export function appendOutput(message: string): void {
  getOutputChannel().append(message);
}

export function appendOutputLine(message: string): void {
  getOutputChannel().appendLine(message);
}

export function showOutput(preserveFocus = true): void {
  getOutputChannel().show(preserveFocus);
}

export function disposeOutputChannel(): void {
  channel?.dispose();
  channel = undefined;
}
