import type { FindingsGroupBy } from "../config/settings";
import { primaryEvidencePath } from "./parser";
import type { Finding } from "./types";

export interface FindingGroup {
  key: string;
  label: string;
  findings: Finding[];
}

const SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"];

export function groupFindings(
  findings: Finding[],
  groupBy: FindingsGroupBy
): FindingGroup[] {
  const buckets = new Map<string, Finding[]>();
  for (const finding of findings) {
    let key: string;
    switch (groupBy) {
      case "domain":
        key = (finding.category || "uncategorized").toLowerCase();
        break;
      case "file":
        key = primaryEvidencePath(finding) || "(no file)";
        break;
      case "rule":
        key = finding.rule_id || "(no rule)";
        break;
      case "severity":
      default:
        key = (finding.severity || "info").toLowerCase();
        break;
    }
    const list = buckets.get(key) ?? [];
    list.push(finding);
    buckets.set(key, list);
  }

  const groups: FindingGroup[] = [...buckets.entries()].map(([key, items]) => ({
    key,
    label: `${key} (${items.length})`,
    findings: items,
  }));

  if (groupBy === "severity") {
    groups.sort((a, b) => {
      const ai = SEVERITY_ORDER.indexOf(a.key);
      const bi = SEVERITY_ORDER.indexOf(b.key);
      return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
    });
  } else {
    groups.sort((a, b) => a.key.localeCompare(b.key));
  }
  return groups;
}

export function filterFindings(findings: Finding[], query: string): Finding[] {
  const needle = query.trim().toLowerCase();
  if (!needle) {
    return findings;
  }
  return findings.filter((finding) => {
    const haystack = [
      finding.title,
      finding.description,
      finding.severity,
      finding.category,
      finding.rule_id,
      finding.id,
      primaryEvidencePath(finding),
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    return haystack.includes(needle);
  });
}
