import * as vscode from "vscode";

import type { ConversationContext } from "../conversation/context";
import type { ExtensionUiState } from "../ui/statusBar";

export class AssessmentStatusProvider implements vscode.TreeDataProvider<string> {
  private readonly emitter = new vscode.EventEmitter<void>();
  readonly onDidChangeTreeData = this.emitter.event;
  private lines: string[] = [
    "State: No assessment",
    "Run CodeStrata: Engineering Assessment to generate Cursor conversation context.",
  ];

  setState(state: ExtensionUiState, detail?: string): void {
    this.lines = [`State: ${state}${detail ? ` — ${detail}` : ""}`];
    if (state === "no-assessment" || state === "engine-missing") {
      this.lines.push("Next: Run Engineering Assessment or Check Environment.");
    }
    this.emitter.fire();
  }

  setFromContext(context: ConversationContext, activeRepo?: string): void {
    this.lines = [
      "State: Assessment available · Context generated",
      activeRepo ? `Active repository: ${activeRepo}` : "Active repository: (selected workspace)",
      `Findings: ${context.findingCount}`,
      `Recommendations: ${context.recommendationCount}`,
      context.truncatedFindings || context.truncatedRecommendations
        ? "Context: truncated for chat window (see full report)"
        : "Context: full selection within limits",
      context.schemaVersion
        ? `Schema: ${context.schemaVersion}`
        : "Schema: unspecified",
      context.engineVersion
        ? `Engine: ${context.engineVersion}`
        : "Engine: unknown",
      context.runDirectory ? `Run: ${context.runDirectory}` : "Run directory: n/a",
      `Context refreshed: ${context.generatedAt}`,
      "Rule: .cursor/rules/codestrata-engineering.mdc",
      "Next: open Cursor Chat / Agent with a suggested question.",
    ];
    this.emitter.fire();
  }

  getTreeItem(element: string): vscode.TreeItem {
    const item = new vscode.TreeItem(element, vscode.TreeItemCollapsibleState.None);
    item.accessibilityInformation = { label: element };
    return item;
  }

  getChildren(): string[] {
    return this.lines;
  }
}
