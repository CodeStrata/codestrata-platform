/**
 * Build repository conversation context from public Engine artifacts only.
 * Never parses source code; never invents findings.
 */

import * as path from "node:path";

import type { Finding, ParsedAssessmentArtifacts, Recommendation } from "../reports/types";

export interface ConversationContextOptions {
  repositoryLabel?: string;
  engineVersion?: string;
  workspaceFolder?: string;
}

export interface ConversationContext {
  generatedAt: string;
  runDirectory?: string;
  schemaVersion?: string;
  engineVersion?: string;
  repositoryLabel?: string;
  findingCount: number;
  recommendationCount: number;
  truncatedFindings: boolean;
  truncatedRecommendations: boolean;
  htmlReportPath?: string;
  summaryLines: string[];
  findings: Finding[];
  recommendations: Recommendation[];
  markdown: string;
  /** Stable content hash body (without timestamp) for skip-unchanged writes. */
  contentFingerprint: string;
}

export const MAX_FINDINGS_IN_CONTEXT = 60;
export const MAX_RECOMMENDATIONS_IN_CONTEXT = 30;
const MAX_DESCRIPTION_CHARS = 320;

const SEVERITY_RANK: Record<string, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  info: 4,
  informational: 4,
};

export function severityRank(severity: string): number {
  return SEVERITY_RANK[severity.toLowerCase()] ?? 50;
}

/** Deterministic: highest severity first, then rule_id, then title, then id. */
export function orderFindings(findings: Finding[]): Finding[] {
  return [...findings].sort((a, b) => {
    const bySeverity = severityRank(a.severity) - severityRank(b.severity);
    if (bySeverity !== 0) {
      return bySeverity;
    }
    const byRule = String(a.rule_id ?? "").localeCompare(String(b.rule_id ?? ""));
    if (byRule !== 0) {
      return byRule;
    }
    const byTitle = a.title.localeCompare(b.title);
    if (byTitle !== 0) {
      return byTitle;
    }
    return a.id.localeCompare(b.id);
  });
}

export function orderRecommendations(recommendations: Recommendation[]): Recommendation[] {
  const priorityRank = (value?: string): number => {
    const normalized = String(value ?? "").toLowerCase();
    if (normalized.includes("p0") || normalized === "critical") {
      return 0;
    }
    if (normalized.includes("p1") || normalized === "high") {
      return 1;
    }
    if (normalized.includes("p2") || normalized === "medium") {
      return 2;
    }
    if (normalized.includes("p3") || normalized === "low") {
      return 3;
    }
    return 40;
  };
  return [...recommendations].sort((a, b) => {
    const byPriority = priorityRank(a.priority) - priorityRank(b.priority);
    if (byPriority !== 0) {
      return byPriority;
    }
    return a.title.localeCompare(b.title) || a.id.localeCompare(b.id);
  });
}

/**
 * Prefer highest-severity findings while retaining domain diversity.
 */
export function selectFindingsForContext(
  findings: Finding[],
  limit = MAX_FINDINGS_IN_CONTEXT
): { selected: Finding[]; truncated: boolean } {
  const ordered = orderFindings(findings);
  if (ordered.length <= limit) {
    return { selected: ordered, truncated: false };
  }
  const selected: Finding[] = [];
  const seenDomains = new Set<string>();
  // Pass 1: one per domain (highest severity already first).
  for (const finding of ordered) {
    if (selected.length >= limit) {
      break;
    }
    const domain = (finding.category || "uncategorized").toLowerCase();
    if (!seenDomains.has(domain)) {
      seenDomains.add(domain);
      selected.push(finding);
    }
  }
  // Pass 2: fill remaining by severity order.
  for (const finding of ordered) {
    if (selected.length >= limit) {
      break;
    }
    if (!selected.some((item) => item.id === finding.id)) {
      selected.push(finding);
    }
  }
  return { selected: orderFindings(selected), truncated: true };
}

export function selectRecommendationsForContext(
  recommendations: Recommendation[],
  limit = MAX_RECOMMENDATIONS_IN_CONTEXT
): { selected: Recommendation[]; truncated: boolean } {
  const ordered = orderRecommendations(recommendations);
  return {
    selected: ordered.slice(0, limit),
    truncated: ordered.length > limit,
  };
}

function relativizePath(
  workspaceFolder: string | undefined,
  absoluteOrRelative: string | undefined
): string | undefined {
  if (!absoluteOrRelative) {
    return undefined;
  }
  if (!workspaceFolder) {
    return absoluteOrRelative;
  }
  if (path.isAbsolute(absoluteOrRelative)) {
    const relative = path.relative(workspaceFolder, absoluteOrRelative);
    if (relative && !relative.startsWith("..") && !path.isAbsolute(relative)) {
      return relative;
    }
  }
  return absoluteOrRelative;
}

export function buildConversationContext(
  artifacts: ParsedAssessmentArtifacts,
  options: ConversationContextOptions = {}
): ConversationContext {
  const findingsPick = selectFindingsForContext(artifacts.findings);
  const recommendationsPick = selectRecommendationsForContext(artifacts.recommendations);
  const reportRel = relativizePath(options.workspaceFolder, artifacts.htmlReportPath);
  const runRel = relativizePath(options.workspaceFolder, artifacts.runDirectory);

  const summaryLines = [
    "Origin: CodeStrata Engine Engineering Assessment public artifacts only.",
    `Findings loaded: ${artifacts.findings.length}; Recommendations loaded: ${artifacts.recommendations.length}.`,
    artifacts.manifest?.schema_version
      ? `Report schema: ${artifacts.manifest.schema_version}.`
      : "Report schema: unspecified (tolerated when major is compatible).",
    options.engineVersion ? `Engine version: ${options.engineVersion}.` : "",
    options.repositoryLabel ? `Repository: ${options.repositoryLabel}.` : "",
    runRel ? `Run directory (workspace-relative when possible): ${runRel}.` : "",
    reportRel ? `Full HTML report: ${reportRel}.` : "",
  ].filter(Boolean);

  const markdown = renderContextMarkdown({
    summaryLines,
    findings: findingsPick.selected,
    recommendations: recommendationsPick.selected,
    truncatedFindings: findingsPick.truncated,
    truncatedRecommendations: recommendationsPick.truncated,
    totalFindings: artifacts.findings.length,
    totalRecommendations: artifacts.recommendations.length,
    reportRel,
  });

  const contentFingerprint = [
    options.repositoryLabel ?? "",
    options.engineVersion ?? "",
    artifacts.manifest?.schema_version ?? "",
    runRel ?? "",
    reportRel ?? "",
    String(artifacts.findings.length),
    String(artifacts.recommendations.length),
    findingsPick.selected.map((f) => `${f.id}:${f.severity}:${f.rule_id ?? ""}`).join("|"),
    recommendationsPick.selected.map((r) => `${r.id}:${r.priority ?? ""}`).join("|"),
  ].join("::");

  return {
    generatedAt: new Date().toISOString(),
    runDirectory: artifacts.runDirectory,
    schemaVersion: artifacts.manifest?.schema_version,
    engineVersion: options.engineVersion,
    repositoryLabel: options.repositoryLabel,
    findingCount: artifacts.findings.length,
    recommendationCount: artifacts.recommendations.length,
    truncatedFindings: findingsPick.truncated,
    truncatedRecommendations: recommendationsPick.truncated,
    htmlReportPath: artifacts.htmlReportPath,
    summaryLines,
    findings: findingsPick.selected,
    recommendations: recommendationsPick.selected,
    markdown,
    contentFingerprint,
  };
}

function truncate(text: string | undefined, max = MAX_DESCRIPTION_CHARS): string {
  if (!text) {
    return "";
  }
  const trimmed = text.trim();
  return trimmed.length <= max ? trimmed : `${trimmed.slice(0, max)}…`;
}

function evidenceHint(finding: Finding): string | undefined {
  for (const evidence of finding.evidence ?? []) {
    if (evidence?.path) {
      const excerpt = evidence.excerpt ? ` · ${truncate(String(evidence.excerpt), 120)}` : "";
      return `${String(evidence.path).trim()}${excerpt}`;
    }
  }
  return undefined;
}

function renderContextMarkdown(input: {
  summaryLines: string[];
  findings: Finding[];
  recommendations: Recommendation[];
  truncatedFindings: boolean;
  truncatedRecommendations: boolean;
  totalFindings: number;
  totalRecommendations: number;
  reportRel?: string;
}): string {
  const lines: string[] = [
    "# CodeStrata Engineering Intelligence (assessment context)",
    "",
    "## Assessment metadata",
    ...input.summaryLines.map((line) => `- ${line}`),
    "",
    "## Findings",
  ];

  if (input.findings.length === 0) {
    lines.push("_No findings in the latest Engineering Assessment._");
  } else {
    for (const finding of input.findings) {
      lines.push(
        `- **[${finding.severity}]** ${finding.title}` +
          (finding.rule_id ? ` (\`${finding.rule_id}\`)` : "") +
          (finding.category ? ` · ${finding.category}` : "")
      );
      const detail = truncate(finding.description);
      if (detail) {
        lines.push(`  - ${detail}`);
      }
      const evidence = evidenceHint(finding);
      if (evidence) {
        lines.push(`  - evidence: \`${evidence}\``);
      }
    }
    if (input.truncatedFindings) {
      lines.push(
        `- _Context truncated: showing ${input.findings.length} of ${input.totalFindings} findings (highest severity + domain diversity). See full report${input.reportRel ? ` at \`${input.reportRel}\`` : ""}._`
      );
    }
  }

  lines.push("", "## Recommendations");
  if (input.recommendations.length === 0) {
    lines.push("_No recommendations in the latest Engineering Assessment._");
  } else {
    for (const rec of input.recommendations) {
      lines.push(
        `- **${rec.title}**` +
          (rec.priority ? ` · priority: ${rec.priority}` : "") +
          (rec.category ? ` · ${rec.category}` : "")
      );
      const detail = truncate(rec.rationale ?? rec.description);
      if (detail) {
        lines.push(`  - ${detail}`);
      }
      if (rec.related_finding_ids?.length) {
        lines.push(`  - related findings: ${rec.related_finding_ids.join(", ")}`);
      }
      if (rec.actions?.length) {
        lines.push(`  - implementation sequence: ${rec.actions.slice(0, 5).join("; ")}`);
      }
    }
    if (input.truncatedRecommendations) {
      lines.push(
        `- _Context truncated: showing ${input.recommendations.length} of ${input.totalRecommendations} recommendations._`
      );
    }
  }

  lines.push(
    "",
    "## Limitations",
    "- This context is a projection of public CodeStrata Engine assessment artifacts.",
    "- Absence of a finding is not proof that an issue does not exist elsewhere.",
    "- Assessment conclusions are not a substitute for inspecting repository source before edits.",
    "- Recommendations may include guidance; distinguish assessment evidence from optional inference.",
    "",
    "## Grounding rules for Cursor Chat / Agent",
    "- Answer from CodeStrata assessment intelligence first.",
    "- For important claims, identify the supporting finding or recommendation (id / rule / title).",
    "- Distinguish fact (artifact text), assessment conclusion, and your inference.",
    "- Never invent rules, findings, evidence paths, severities, or recommendations.",
    "- If the assessment lacks enough information, say so explicitly.",
    "- Inspect repository code before suggesting exact edits.",
    "- Do not claim a fix was applied unless files were actually modified in this session.",
    "- Preserve developer control; propose plans rather than asserting irreversible changes.",
    "- Do not claim Platform, Portfolio Intelligence, Executive Intelligence, or Repository Retrieval capabilities.",
    ""
  );
  return lines.join("\n");
}
