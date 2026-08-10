/**
 * Build Engine publish args and parse public URL (Slice 17.21).
 */

import * as path from "node:path";

import { REPORT_PUBLISH_POLICY } from "./policy";

export type PublishArgsInput = {
  readonly repositoryId: string;
  /** Workspace-relative or absolute artifacts root (.codestrata-artifacts). */
  readonly artifactsRoot: string;
  readonly acknowledgePrivate: boolean;
  readonly reportType?: "assessment" | "eir";
};

/**
 * Derive logical repository id from …/assessments/<repo-id>/current/assessment.html.
 */
export function repositoryIdFromHtmlPath(htmlPath: string): string | undefined {
  const normalized = path.normalize(htmlPath);
  const parts = normalized.split(path.sep);
  const currentIdx = parts.lastIndexOf("current");
  if (currentIdx <= 0) {
    return undefined;
  }
  const repoId = parts[currentIdx - 1];
  if (!repoId || repoId === "assessments" || repoId === "." || repoId === "..") {
    return undefined;
  }
  return repoId;
}

export function isLocalOrPrivateRepositoryId(repositoryId: string): boolean {
  return repositoryId.startsWith("local-");
}

/**
 * Map assessment outputDirectory (.codestrata-artifacts/assessments) → artifacts root.
 */
export function artifactsRootFromOutputDirectory(outputDirectory: string): string {
  const normalized = outputDirectory.replace(/\\/g, "/").replace(/\/+$/, "");
  if (normalized.endsWith("/assessments") || normalized === "assessments") {
    const parent = path.dirname(normalized);
    return parent === "." ? ".codestrata-artifacts" : parent;
  }
  if (normalized.endsWith(".codestrata-artifacts")) {
    return normalized;
  }
  return path.join(normalized, "..");
}

export function buildReportPublishArgs(input: PublishArgsInput): string[] {
  const args = [
    "report",
    "publish",
    "--type",
    input.reportType ?? "assessment",
    "--repository-id",
    input.repositoryId,
    "--artifacts-root",
    input.artifactsRoot,
    "--confirm-public-publish",
  ];
  if (input.acknowledgePrivate) {
    args.push("--acknowledge-private-repository");
  }
  return args;
}

/**
 * Extract branded public URL from Engine CLI stdout/stderr.
 * Rejects raw S3 / execute-api hosts.
 */
export function parsePublicReportUrl(combinedOutput: string): string | undefined {
  const match = combinedOutput.match(
    /https:\/\/reports\.codestrata\.ai\/r\/[A-Za-z0-9._~-]+/
  );
  if (!match) {
    return undefined;
  }
  const url = match[0];
  if (
    /s3\.amazonaws\.com|execute-api\.|cloudfront\.net/i.test(combinedOutput) &&
    !url.startsWith(REPORT_PUBLISH_POLICY.public_url_prefix)
  ) {
    return undefined;
  }
  if (!url.startsWith(REPORT_PUBLISH_POLICY.public_url_prefix)) {
    return undefined;
  }
  return url;
}

export function publishEnvWithTelemetryOptIn(
  baseEnv: NodeJS.ProcessEnv = process.env
): NodeJS.ProcessEnv {
  return {
    ...baseEnv,
    CODESTRATA_TELEMETRY_OPT_IN: "true",
  };
}
