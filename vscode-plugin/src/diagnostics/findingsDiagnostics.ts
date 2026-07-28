import * as vscode from "vscode";

import { primaryEvidenceExcerpt, primaryEvidencePath } from "../reports/parser";
import type { Finding } from "../reports/types";
import { extractEvidenceLine, resolveWorkspaceRelativePath } from "../workspace/paths";

/**
 * Severity mapping (documented, deterministic):
 * critical/high → Error; medium → Warning; else Information.
 */
export function mapFindingSeverity(severity: string): vscode.DiagnosticSeverity {
  switch (severity.toLowerCase()) {
    case "critical":
    case "high":
      return vscode.DiagnosticSeverity.Error;
    case "medium":
      return vscode.DiagnosticSeverity.Warning;
    default:
      return vscode.DiagnosticSeverity.Information;
  }
}

export class FindingsDiagnostics implements vscode.Disposable {
  private readonly collection: vscode.DiagnosticCollection;

  constructor() {
    this.collection = vscode.languages.createDiagnosticCollection("codestrata");
  }

  clear(): void {
    this.collection.clear();
  }

  publish(workspaceFolder: string, findings: Finding[]): void {
    this.collection.clear();
    const byFile = new Map<string, vscode.Diagnostic[]>();
    const seen = new Set<string>();
    for (const finding of findings) {
      const relative = primaryEvidencePath(finding);
      if (!relative) {
        continue;
      }
      const resolved = resolveWorkspaceRelativePath(workspaceFolder, relative);
      if (!resolved?.insideWorkspace) {
        continue;
      }
      const dedupeKey = `${resolved.path}::${finding.id}`;
      if (seen.has(dedupeKey)) {
        continue;
      }
      seen.add(dedupeKey);
      const uri = vscode.Uri.file(resolved.path);
      const line = extractEvidenceLine(primaryEvidenceExcerpt(finding)) ?? 1;
      const lineIndex = Math.max(0, line - 1);
      const diagnostic = new vscode.Diagnostic(
        new vscode.Range(lineIndex, 0, lineIndex, 200),
        `${finding.title}${finding.rule_id ? ` (${finding.rule_id})` : ""}`,
        mapFindingSeverity(finding.severity)
      );
      diagnostic.source = "CodeStrata";
      diagnostic.code = finding.rule_id ?? finding.id;
      const list = byFile.get(uri.toString()) ?? [];
      list.push(diagnostic);
      byFile.set(uri.toString(), list);
    }
    for (const [uriString, diagnostics] of byFile) {
      this.collection.set(vscode.Uri.parse(uriString), diagnostics);
    }
  }

  dispose(): void {
    this.collection.dispose();
  }
}
