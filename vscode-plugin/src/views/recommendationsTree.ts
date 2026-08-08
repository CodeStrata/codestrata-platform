import * as vscode from "vscode";

import type { Recommendation } from "../reports/types";
import {
  EMPTY_RECOMMENDATIONS_DESCRIPTION,
  EMPTY_RECOMMENDATIONS_TITLE,
} from "../ui/presentationCopy";

export class RecommendationItem extends vscode.TreeItem {
  constructor(public readonly recommendation: Recommendation) {
    super(recommendation.title, vscode.TreeItemCollapsibleState.None);
    const bits = [
      recommendation.priority,
      recommendation.category,
      recommendation.related_finding_ids?.length
        ? `${recommendation.related_finding_ids.length} findings`
        : undefined,
    ].filter(Boolean);
    this.description = bits.join(" · ");
    this.tooltip = new vscode.MarkdownString(
      [
        `**${recommendation.title}**`,
        recommendation.priority ? `Priority: ${recommendation.priority}` : undefined,
        recommendation.category ? `Domain: ${recommendation.category}` : undefined,
        recommendation.effort ? `Effort: ${recommendation.effort}` : undefined,
        recommendation.risk ? `Risk: ${recommendation.risk}` : undefined,
        recommendation.rationale ? `\n${recommendation.rationale}` : undefined,
        recommendation.description ? `\n${recommendation.description}` : undefined,
        recommendation.related_finding_ids?.length
          ? `\nAssociated findings: ${recommendation.related_finding_ids.join(", ")}`
          : undefined,
        recommendation.actions?.length
          ? `\nGuidance:\n- ${recommendation.actions.join("\n- ")}`
          : undefined,
      ]
        .filter(Boolean)
        .join("\n\n")
    );
    this.iconPath = new vscode.ThemeIcon("lightbulb");
    this.contextValue = "codestrataRecommendation";
    this.accessibilityInformation = {
      label: `Recommendation ${recommendation.title}${
        recommendation.priority ? `, priority ${recommendation.priority}` : ""
      }`,
    };
  }
}

export class RecommendationsTreeProvider
  implements vscode.TreeDataProvider<RecommendationItem>, vscode.Disposable
{
  private readonly _onDidChangeTreeData = new vscode.EventEmitter<
    RecommendationItem | undefined | null | void
  >();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;
  private recommendations: Recommendation[] = [];

  setRecommendations(items: Recommendation[]): void {
    this.recommendations = items;
    this._onDidChangeTreeData.fire();
  }

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: RecommendationItem): vscode.TreeItem {
    return element;
  }

  getChildren(): RecommendationItem[] {
    if (this.recommendations.length === 0) {
      const empty = new RecommendationItem({
        id: "empty",
        title: EMPTY_RECOMMENDATIONS_TITLE,
        description: EMPTY_RECOMMENDATIONS_DESCRIPTION,
      });
      empty.iconPath = new vscode.ThemeIcon("info");
      empty.contextValue = "codestrataRecommendationEmpty";
      return [empty];
    }
    return this.recommendations.map((item) => new RecommendationItem(item));
  }

  dispose(): void {
    this._onDidChangeTreeData.dispose();
  }
}
