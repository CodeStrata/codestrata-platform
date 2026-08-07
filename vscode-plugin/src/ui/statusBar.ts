import * as vscode from "vscode";

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
    this.item.tooltip = "CodeStrata Engine — Run Assessment";
    this.item.accessibilityInformation = {
      label: "CodeStrata idle. Activate to run Engineering Assessment.",
      role: "button",
    };
  }

  setRunning(): void {
    this.item.text = "$(sync~spin) CodeStrata";
    this.item.tooltip = "Engineering Assessment in progress…";
    this.item.accessibilityInformation = {
      label: "CodeStrata Engineering Assessment in progress",
      role: "button",
    };
  }

  setReady(findingsCount: number): void {
    this.item.text = `$(check) CodeStrata ${findingsCount}`;
    this.item.tooltip = `Latest Engineering Assessment: ${findingsCount} findings`;
    this.item.accessibilityInformation = {
      label: `CodeStrata ready. Latest Engineering Assessment has ${findingsCount} findings.`,
      role: "button",
    };
  }

  setError(message: string): void {
    this.item.text = "$(error) CodeStrata";
    this.item.tooltip = message;
    this.item.accessibilityInformation = {
      label: `CodeStrata error: ${message}`,
      role: "button",
    };
  }

  dispose(): void {
    this.item.dispose();
  }
}
