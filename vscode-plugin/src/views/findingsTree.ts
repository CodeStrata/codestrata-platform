import * as path from "node:path";

import * as vscode from "vscode";

import type { FindingsGroupBy } from "../config/settings";
import { filterFindings, groupFindings } from "../reports/findingsModel";
import { primaryEvidencePath } from "../reports/parser";
import type { Finding } from "../reports/types";

export type FindingsTreeNode = FindingGroupNode | FindingItemNode;

export class FindingGroupNode extends vscode.TreeItem {
  constructor(
    public readonly groupKey: string,
    label: string,
    public readonly findings: Finding[]
  ) {
    super(label, vscode.TreeItemCollapsibleState.Expanded);
    this.contextValue = "codestrataFindingGroup";
    this.iconPath = new vscode.ThemeIcon("folder");
  }
}

export class FindingItemNode extends vscode.TreeItem {
  constructor(public readonly finding: Finding) {
    super(finding.title, vscode.TreeItemCollapsibleState.None);
    this.description = [finding.severity, finding.rule_id].filter(Boolean).join(" · ");
    this.tooltip = [
      finding.title,
      finding.severity,
      finding.rule_id,
      finding.description,
    ]
      .filter(Boolean)
      .join("\n");
    this.contextValue = "codestrataFinding";
    this.iconPath = new vscode.ThemeIcon("warning");
    this.accessibilityInformation = {
      label: `Finding ${finding.title}, severity ${finding.severity}${
        finding.rule_id ? `, rule ${finding.rule_id}` : ""
      }`,
    };
    this.command = {
      command: "codestrata.openFindingLocation",
      title: "Open Finding Location",
      arguments: [finding],
    };
  }
}

export class FindingsTreeProvider
  implements vscode.TreeDataProvider<FindingsTreeNode>, vscode.Disposable
{
  private readonly _onDidChangeTreeData = new vscode.EventEmitter<
    FindingsTreeNode | undefined | null | void
  >();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  private findings: Finding[] = [];
  private groupBy: FindingsGroupBy = "severity";
  private filterQuery = "";
  private workspaceFolder: string | undefined;

  constructor() {}

  setWorkspaceFolder(folder: string | undefined): void {
    this.workspaceFolder = folder;
  }

  setGroupBy(groupBy: FindingsGroupBy): void {
    this.groupBy = groupBy;
    this.refresh();
  }

  setFilter(query: string): void {
    this.filterQuery = query;
    this.refresh();
  }

  setFindings(findings: Finding[]): void {
    this.findings = findings;
    this.refresh();
  }

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: FindingsTreeNode): vscode.TreeItem {
    return element;
  }

  getChildren(element?: FindingsTreeNode): FindingsTreeNode[] {
    if (element instanceof FindingGroupNode) {
      return element.findings.map((finding) => new FindingItemNode(finding));
    }
    const filtered = filterFindings(this.findings, this.filterQuery);
    if (filtered.length === 0) {
      const empty = new FindingGroupNode(
        "empty",
        this.findings.length === 0
          ? "No findings loaded — run Engineering Assessment"
          : "No findings match the current filter",
        []
      );
      empty.collapsibleState = vscode.TreeItemCollapsibleState.None;
      empty.iconPath = new vscode.ThemeIcon("info");
      empty.accessibilityInformation = {
        label: empty.label?.toString() ?? "No findings",
      };
      return [empty];
    }
    return groupFindings(filtered, this.groupBy).map(
      (group) => new FindingGroupNode(group.key, group.label, group.findings)
    );
  }

  resolveWorkspacePath(relativeOrAbsolute: string): string {
    if (path.isAbsolute(relativeOrAbsolute)) {
      return relativeOrAbsolute;
    }
    if (!this.workspaceFolder) {
      return relativeOrAbsolute;
    }
    return path.join(this.workspaceFolder, relativeOrAbsolute);
  }

  evidencePathFor(finding: Finding): string | undefined {
    const relative = primaryEvidencePath(finding);
    return relative ? this.resolveWorkspacePath(relative) : undefined;
  }

  dispose(): void {
    this._onDidChangeTreeData.dispose();
  }
}
