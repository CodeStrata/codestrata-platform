import * as fs from "node:fs";
import * as path from "node:path";

import {
  findLatestHtmlRunDirectory,
  resolveApprovedOutputRoot,
} from "../reportOpening";
import { checkReportSchemaVersion } from "./schema";
import type {
  Finding,
  ParsedAssessmentArtifacts,
  Recommendation,
  ReportManifest,
} from "./types";

function asRecord(value: unknown): Record<string, unknown> | undefined {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : undefined;
}

function readJsonSafe(filePath: string): { value?: unknown; error?: string } {
  try {
    return { value: JSON.parse(fs.readFileSync(filePath, "utf8")) };
  } catch (error) {
    return { error: `Malformed JSON in ${path.basename(filePath)}: ${String(error)}` };
  }
}

export function normalizeFindings(payload: unknown): Finding[] {
  const root = asRecord(payload);
  const list = Array.isArray(payload)
    ? payload
    : Array.isArray(root?.findings)
      ? root.findings
      : Array.isArray(asRecord(root?.assessment)?.findings)
        ? (asRecord(root?.assessment)?.findings as unknown[])
        : [];
  const findings: Finding[] = [];
  for (const item of list) {
    const row = asRecord(item);
    if (!row) {
      continue;
    }
    const id = String(row.id ?? row.finding_id ?? "").trim();
    const title = String(row.title ?? "Finding").trim();
    if (!id && !title) {
      continue;
    }
    findings.push({
      id: id || title,
      title,
      description: row.description != null ? String(row.description) : undefined,
      severity: String(row.severity ?? "info").toLowerCase(),
      category: row.category != null ? String(row.category) : undefined,
      rule_id: row.rule_id != null ? String(row.rule_id) : undefined,
      evidence: Array.isArray(row.evidence)
        ? (row.evidence as Finding["evidence"])
        : undefined,
    });
  }
  return findings;
}

export function normalizeRecommendations(payload: unknown): Recommendation[] {
  const root = asRecord(payload);
  const assessment = asRecord(root?.assessment);
  const list = Array.isArray(payload)
    ? payload
    : Array.isArray(root?.recommendations)
      ? root.recommendations
      : Array.isArray(assessment?.deterministic_recommendations)
        ? (assessment?.deterministic_recommendations as unknown[])
        : Array.isArray(assessment?.recommendations)
          ? (assessment?.recommendations as unknown[])
          : [];
  const recommendations: Recommendation[] = [];
  for (const item of list) {
    const row = asRecord(item);
    if (!row) {
      continue;
    }
    const id = String(row.id ?? "").trim();
    const title = String(row.title ?? "Recommendation").trim();
    if (!id && !title) {
      continue;
    }
    recommendations.push({
      id: id || title,
      title,
      description: row.description != null ? String(row.description) : undefined,
      rationale: row.rationale != null ? String(row.rationale) : undefined,
      priority: row.priority != null ? String(row.priority) : undefined,
      category: row.category != null ? String(row.category) : undefined,
      rule_id: row.rule_id != null ? String(row.rule_id) : undefined,
      related_finding_ids: Array.isArray(row.related_finding_ids)
        ? row.related_finding_ids.map((value) => String(value))
        : undefined,
      effort: row.effort != null ? String(row.effort) : undefined,
      risk: row.risk != null ? String(row.risk) : undefined,
      actions: Array.isArray(row.actions)
        ? row.actions.map((value) => String(value))
        : undefined,
    });
  }
  return recommendations;
}

export function primaryEvidencePath(finding: Finding): string | undefined {
  for (const evidence of finding.evidence ?? []) {
    const candidate = evidence?.path;
    if (candidate && String(candidate).trim()) {
      return String(candidate).trim();
    }
  }
  return undefined;
}

export function primaryEvidenceExcerpt(finding: Finding): string | undefined {
  for (const evidence of finding.evidence ?? []) {
    if (evidence?.path && evidence.excerpt) {
      return String(evidence.excerpt);
    }
  }
  return finding.evidence?.[0]?.excerpt
    ? String(finding.evidence[0].excerpt)
    : undefined;
}

export function loadArtifactsFromRunDirectory(
  runDirectory: string
): ParsedAssessmentArtifacts {
  const htmlReportPath = path.join(runDirectory, "report.html");
  const jsonReportPath = path.join(runDirectory, "report.json");
  const findingsPath = path.join(runDirectory, "findings.json");
  const recommendationsPath = path.join(runDirectory, "recommendations.json");
  const parseWarnings: string[] = [];

  let findings: Finding[] = [];
  let recommendations: Recommendation[] = [];
  let manifest: ReportManifest | undefined;
  let schemaError: string | undefined;

  if (fs.existsSync(findingsPath)) {
    const parsed = readJsonSafe(findingsPath);
    if (parsed.error) {
      parseWarnings.push(parsed.error);
    } else {
      findings = normalizeFindings(parsed.value);
    }
  }
  if (fs.existsSync(recommendationsPath)) {
    const parsed = readJsonSafe(recommendationsPath);
    if (parsed.error) {
      parseWarnings.push(parsed.error);
    } else {
      recommendations = normalizeRecommendations(parsed.value);
    }
  }
  if (fs.existsSync(jsonReportPath)) {
    const parsed = readJsonSafe(jsonReportPath);
    if (parsed.error) {
      parseWarnings.push(parsed.error);
    } else {
      const report = parsed.value;
      const root = asRecord(report);
      if (findings.length === 0) {
        findings = normalizeFindings(report);
      }
      if (recommendations.length === 0) {
        recommendations = normalizeRecommendations(report);
      }
      const manifestRaw = asRecord(root?.manifest);
      if (manifestRaw) {
        manifest = {
          schema_version:
            manifestRaw.schema_version != null
              ? String(manifestRaw.schema_version)
              : undefined,
          product_name:
            manifestRaw.product_name != null ? String(manifestRaw.product_name) : undefined,
          edition: manifestRaw.edition != null ? String(manifestRaw.edition) : undefined,
          report_type:
            manifestRaw.report_type != null ? String(manifestRaw.report_type) : undefined,
          brand_report_name:
            manifestRaw.brand_report_name != null
              ? String(manifestRaw.brand_report_name)
              : undefined,
          generation_mode:
            manifestRaw.generation_mode != null
              ? String(manifestRaw.generation_mode)
              : undefined,
        };
        const schema = checkReportSchemaVersion(manifest.schema_version);
        if (!schema.ok) {
          schemaError = schema.reason;
        }
      }
    }
  } else if (!fs.existsSync(findingsPath) && !fs.existsSync(htmlReportPath)) {
    parseWarnings.push("No report.json, findings.json, or report.html in run directory.");
  }

  return {
    runDirectory,
    htmlReportPath: fs.existsSync(htmlReportPath) ? htmlReportPath : undefined,
    jsonReportPath: fs.existsSync(jsonReportPath) ? jsonReportPath : undefined,
    findingsPath: fs.existsSync(findingsPath) ? findingsPath : undefined,
    findings,
    recommendations,
    manifest,
    schemaError,
    parseWarnings,
  };
}

export function findLatestRunDirectory(
  workspaceFolder: string,
  outputDirectory: string
): string | undefined {
  // Slice 13.7: contained HTML-only discovery (no JSON-only runs, no symlink dirs).
  const output = resolveApprovedOutputRoot(workspaceFolder, outputDirectory);
  if (!output.contained) {
    return undefined;
  }
  return findLatestHtmlRunDirectory(workspaceFolder, output.outputRoot);
}
