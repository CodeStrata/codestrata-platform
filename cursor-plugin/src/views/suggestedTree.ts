import * as vscode from "vscode";

import type { ConversationContext } from "../conversation/context";
import {
  questionsByCategory,
  type PromptCategory,
  type SuggestedQuestion,
} from "../conversation/suggestedQuestions";

type TreeNode =
  | { kind: "category"; category: PromptCategory }
  | { kind: "question"; question: SuggestedQuestion };

export class SuggestedQuestionsProvider implements vscode.TreeDataProvider<TreeNode> {
  private readonly emitter = new vscode.EventEmitter<TreeNode | undefined>();
  readonly onDidChangeTreeData = this.emitter.event;
  private hasAssessment = false;

  setHasAssessment(hasAssessment: boolean): void {
    this.hasAssessment = hasAssessment;
    this.emitter.fire(undefined);
  }

  refresh(): void {
    this.emitter.fire(undefined);
  }

  getTreeItem(element: TreeNode): vscode.TreeItem {
    if (element.kind === "category") {
      const item = new vscode.TreeItem(
        element.category,
        vscode.TreeItemCollapsibleState.Expanded
      );
      item.accessibilityInformation = {
        label: `Suggested question category ${element.category}`,
      };
      return item;
    }
    const question = element.question;
    const item = new vscode.TreeItem(
      question.title,
      vscode.TreeItemCollapsibleState.None
    );
    item.description = this.hasAssessment ? question.purpose : "Requires assessment";
    item.tooltip = this.hasAssessment
      ? `${question.purpose}\n\n${question.prompt}`
      : "Run CodeStrata: Engineering Assessment before using this prompt.";
    item.iconPath = new vscode.ThemeIcon(
      this.hasAssessment ? "comment-discussion" : "circle-slash"
    );
    item.accessibilityInformation = {
      label: this.hasAssessment
        ? `Suggested question: ${question.title}. ${question.purpose}`
        : `Suggested question disabled until assessment: ${question.title}`,
    };
    if (this.hasAssessment) {
      item.command = {
        command: "codestrata.askSuggested",
        title: "Ask in Cursor",
        arguments: [question],
      };
    } else {
      item.command = {
        command: "codestrata.missingAssessmentHelp",
        title: "Assessment required",
        arguments: [],
      };
    }
    return item;
  }

  getChildren(element?: TreeNode): TreeNode[] {
    if (!element) {
      return [...questionsByCategory().keys()].map((category) => ({
        kind: "category" as const,
        category,
      }));
    }
    if (element.kind === "category") {
      return (questionsByCategory().get(element.category) ?? []).map((question) => ({
        kind: "question" as const,
        question,
      }));
    }
    return [];
  }
}
