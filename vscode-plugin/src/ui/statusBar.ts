import * as vscode from "vscode";

import {
  STATUS_A11Y_READY,
  STATUS_A11Y_RUNNING,
  STATUS_TOOLTIP_READY,
  STATUS_TOOLTIP_RUNNING,
} from "./presentationCopy";

export class StatusBarController implements vscode.Disposable {
  private readonly item: vscode.StatusBarItem;

  constructor() {
    this.item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    this.item.command = "codestrata.assess";
    this.setIdle();
    this.item.show();
  }

  setIdle(): void {
    this.item.text = "$(pulse) CodeStrata";
    this.item.tooltip = STATUS_TOOLTIP_READY;
    this.item.accessibilityInformation = {
      label: STATUS_A11Y_READY,
      role: "button",
    };
  }

  setRunning(): void {
    this.item.text = "$(sync~spin) CodeStrata";
    this.item.tooltip = STATUS_TOOLTIP_RUNNING;
    this.item.accessibilityInformation = {
      label: STATUS_A11Y_RUNNING,
      role: "button",
    };
  }

  setReady(findingsCount: number): void {
    this.item.text = `$(check) CodeStrata ${findingsCount}`;
    this.item.tooltip = `CodeStrata — Ready. Latest assessment: ${findingsCount} findings.`;
    this.item.accessibilityInformation = {
      label: `CodeStrata ready. Latest assessment has ${findingsCount} findings.`,
      role: "button",
    };
  }

  setError(message: string): void {
    this.item.text = "$(error) CodeStrata";
    this.item.tooltip = `CodeStrata — Action required. ${message}`;
    this.item.accessibilityInformation = {
      label: `CodeStrata action required: ${message}`,
      role: "button",
    };
  }

  dispose(): void {
    this.item.dispose();
  }
}
