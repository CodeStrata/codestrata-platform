import * as vscode from "vscode";

export type ExtensionUiState =
  | "engine-missing"
  | "engine-incompatible"
  | "ready"
  | "running"
  | "cancelled"
  | "failed"
  | "available"
  | "context-generated"
  | "context-outdated"
  | "no-assessment";

export class StatusBarController implements vscode.Disposable {
  private readonly item: vscode.StatusBarItem;
  private state: ExtensionUiState = "no-assessment";

  constructor() {
    this.item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    this.item.command = "codestrata.assess";
    this.setState("no-assessment");
    this.item.show();
  }

  getState(): ExtensionUiState {
    return this.state;
  }

  setState(state: ExtensionUiState, detail?: string): void {
    this.state = state;
    switch (state) {
      case "engine-missing":
        this.item.text = "$(warning) CodeStrata";
        this.item.tooltip = detail ?? "CodeStrata Engine not found";
        break;
      case "engine-incompatible":
        this.item.text = "$(warning) CodeStrata";
        this.item.tooltip = detail ?? "CodeStrata Engine incompatible";
        break;
      case "ready":
        this.item.text = "$(pulse) CodeStrata";
        this.item.tooltip = "CodeStrata Engine ready — Run Engineering Assessment";
        break;
      case "running":
        this.item.text = "$(sync~spin) CodeStrata";
        this.item.tooltip = "Engineering Assessment in progress…";
        break;
      case "cancelled":
        this.item.text = "$(circle-slash) CodeStrata";
        this.item.tooltip = "Engineering Assessment cancelled";
        break;
      case "failed":
        this.item.text = "$(error) CodeStrata";
        this.item.tooltip = detail ?? "Engineering Assessment failed";
        break;
      case "available":
      case "context-generated":
        this.item.text = `$(check) CodeStrata ${detail ?? ""}`.trim();
        this.item.tooltip =
          detail ??
          "Assessment available — Cursor conversation context generated";
        break;
      case "context-outdated":
        this.item.text = "$(history) CodeStrata";
        this.item.tooltip = "Assessment context may be outdated — refresh";
        break;
      case "no-assessment":
      default:
        this.item.text = "$(pulse) CodeStrata";
        this.item.tooltip = "No Engineering Assessment — run CodeStrata: Engineering Assessment";
        break;
    }
    this.item.accessibilityInformation = {
      label: `CodeStrata status: ${state}${detail ? ` — ${detail}` : ""}`,
      role: "button",
    };
  }

  setIdle(): void {
    this.setState("no-assessment");
  }

  setRunning(): void {
    this.setState("running");
  }

  setReady(findingsCount: number): void {
    this.setState(
      "context-generated",
      `${findingsCount} findings · context ready for Cursor`
    );
  }

  setError(message: string): void {
    this.setState("failed", message);
  }

  dispose(): void {
    this.item.dispose();
  }
}
