/**
 * Report location and open orchestration (Slice 13.7).
 *
 * Engine remains sole report generator. Extension only locates/opens locally.
 */

import * as fs from "node:fs";
import * as path from "node:path";

import {
  htmlPathForRunDirectory,
  resolveApprovedOutputRoot,
  resolveContainedPath,
  validateHtmlReportFile,
} from "./containment";
import { ENGINE_HTML_REPORT_BASENAME } from "./policy";
import {
  createReportOpeningResult,
  type ReportOpeningResult,
} from "./results";
import type { ReportOpeningDiagnostics } from "./diagnostics";
import { REPORT_OPENING_POLICY_VERSION } from "./policy";
import { DEFAULT_REPORT_OPENING_LIMITATIONS } from "./policy";

export type LocateReportInput = {
  readonly workspaceRoot: string;
  readonly outputDirectory: string;
  /** Preferred Engine run directory from JSON summary (post-assessment). */
  readonly preferredRunDirectory?: string;
  /** Session-cached HTML path from last successful assessment. */
  readonly sessionHtmlPath?: string;
};

export type LocateReportOutcome = {
  readonly status:
    | "available"
    | "missing"
    | "unsafe_path"
    | "invalid_file"
    | "ambiguous";
  /** Private runtime path — never put in public diagnostics. */
  readonly htmlPath?: string;
  readonly runDirectory?: string;
};

/**
 * Locate a single canonical HTML report within the approved output boundary.
 * Bounded search: `<output>/<repo>/<run>/report.html` only (depth 2).
 * Requires report.html (not JSON-only runs).
 */
export function locateHtmlReport(
  input: LocateReportInput
): LocateReportOutcome {
  const output = resolveApprovedOutputRoot(
    input.workspaceRoot,
    input.outputDirectory
  );
  if (!output.contained) {
    return { status: "unsafe_path" };
  }

  // Prefer session HTML (same assessment) when valid.
  if (input.sessionHtmlPath) {
    const validated = validateHtmlReportFile({
      workspaceRoot: input.workspaceRoot,
      outputDirectory: input.outputDirectory,
      candidatePath: input.sessionHtmlPath,
    });
    if (validated.ok) {
      return {
        status: "available",
        htmlPath: validated.path,
        runDirectory: path.dirname(validated.path),
      };
    }
  }

  // Prefer Engine-provided run directory after successful assessment.
  if (input.preferredRunDirectory) {
    const runResolved = resolveContainedPath(
      output.outputRoot,
      path.isAbsolute(input.preferredRunDirectory)
        ? input.preferredRunDirectory
        : path.join(input.workspaceRoot, input.preferredRunDirectory)
    );
    if (!runResolved.contained) {
      return { status: "unsafe_path" };
    }
    const html = htmlPathForRunDirectory(runResolved.path);
    const validated = validateHtmlReportFile({
      workspaceRoot: input.workspaceRoot,
      outputDirectory: input.outputDirectory,
      candidatePath: html,
    });
    if (validated.ok) {
      return {
        status: "available",
        htmlPath: validated.path,
        runDirectory: runResolved.path,
      };
    }
    if (validated.reason === "missing") {
      return { status: "missing" };
    }
    return {
      status:
        validated.reason === "unsafe_path" ||
        validated.reason === "symlink_escape"
          ? "unsafe_path"
          : "invalid_file",
    };
  }

  // Explicit open / fallback: newest run under output that contains report.html.
  const latest = findLatestHtmlRunDirectory(
    input.workspaceRoot,
    output.outputRoot
  );
  if (!latest) {
    return { status: "missing" };
  }
  const validated = validateHtmlReportFile({
    workspaceRoot: input.workspaceRoot,
    outputDirectory: input.outputDirectory,
    candidatePath: htmlPathForRunDirectory(latest),
  });
  if (!validated.ok) {
    return {
      status:
        validated.reason === "missing"
          ? "missing"
          : validated.reason === "unsafe_path" ||
              validated.reason === "symlink_escape"
            ? "unsafe_path"
            : "invalid_file",
    };
  }
  return {
    status: "available",
    htmlPath: validated.path,
    runDirectory: latest,
  };
}

/**
 * Bounded discovery for Slice 17.12 flat runs:
 *   `<outputRoot>/<run-id>/assessment.html`
 * plus legacy nested:
 *   `<outputRoot>/<repo>/<run>/report.html`
 */
export function findLatestHtmlRunDirectory(
  workspaceRoot: string,
  outputRoot: string
): string | undefined {
  const containedRoot = resolveContainedPath(workspaceRoot, outputRoot);
  if (!containedRoot.contained) {
    return undefined;
  }
  const root = containedRoot.path;
  if (!fs.existsSync(root)) {
    return undefined;
  }
  const candidates: { dir: string; mtime: number }[] = [];

  const considerRun = (runPath: string, stat: fs.Stats): void => {
    const htmlModern = path.join(runPath, "assessment.html");
    const htmlLegacy = path.join(runPath, "report.html");
    const html = fs.existsSync(htmlModern) ? htmlModern : htmlLegacy;
    if (!fs.existsSync(html)) {
      return;
    }
    try {
      const htmlLstat = fs.lstatSync(html);
      if (htmlLstat.isSymbolicLink() || !htmlLstat.isFile()) {
        return;
      }
    } catch {
      return;
    }
    const contained = resolveContainedPath(root, html);
    if (!contained.contained) {
      return;
    }
    candidates.push({ dir: runPath, mtime: stat.mtimeMs });
  };

  let topNames: string[];
  try {
    topNames = fs.readdirSync(root);
  } catch {
    return undefined;
  }
  for (const topName of topNames) {
    const topPath = path.join(root, topName);
    let topStat: fs.Stats;
    try {
      topStat = fs.lstatSync(topPath);
    } catch {
      continue;
    }
    if (topStat.isSymbolicLink() || !topStat.isDirectory()) {
      continue;
    }
    // Flat Slice 17.12 run directory
    if (
      fs.existsSync(path.join(topPath, "assessment.html")) ||
      fs.existsSync(path.join(topPath, "report.html"))
    ) {
      considerRun(topPath, topStat);
      continue;
    }
    // Legacy nested repo/run
    let runNames: string[];
    try {
      runNames = fs.readdirSync(topPath);
    } catch {
      continue;
    }
    for (const runName of runNames) {
      const runPath = path.join(topPath, runName);
      let stat: fs.Stats;
      try {
        stat = fs.lstatSync(runPath);
      } catch {
        continue;
      }
      if (stat.isSymbolicLink() || !stat.isDirectory()) {
        continue;
      }
      considerRun(runPath, stat);
    }
  }
  candidates.sort((a, b) => b.mtime - a.mtime);
  return candidates[0]?.dir;
}

export type OpenHtmlAdapter = {
  openLocalFile(absolutePath: string): Promise<boolean>;
};

/**
 * Validate then open. Re-checks existence immediately before open (TOCTOU).
 * Never parses HTML contents.
 */
export async function openValidatedHtmlReport(options: {
  readonly workspaceRoot: string;
  readonly outputDirectory: string;
  readonly htmlPath: string | undefined;
  readonly open: OpenHtmlAdapter;
  readonly reportExpected?: boolean;
}): Promise<ReportOpeningResult> {
  const validated = validateHtmlReportFile({
    workspaceRoot: options.workspaceRoot,
    outputDirectory: options.outputDirectory,
    candidatePath: options.htmlPath,
  });
  if (!validated.ok) {
    const status =
      validated.reason === "missing"
        ? "missing"
        : validated.reason === "unsafe_path" ||
            validated.reason === "symlink_escape"
          ? "unsafe_path"
          : "invalid_file";
    return createReportOpeningResult({
      status,
      report_expected: options.reportExpected ?? true,
      report_available: false,
      open_attempted: false,
      open_succeeded: false,
      user_action_required: status === "missing",
      recovery_category:
        status === "missing" ? "rerun_assessment" : "inspect_output",
    });
  }
  // TOCTOU: re-stat immediately before open.
  try {
    const again = fs.statSync(validated.path);
    if (!again.isFile()) {
      return createReportOpeningResult({
        status: "missing",
        report_expected: options.reportExpected ?? true,
        report_available: false,
        open_attempted: true,
        open_succeeded: false,
        user_action_required: true,
        recovery_category: "rerun_assessment",
      });
    }
  } catch {
    return createReportOpeningResult({
      status: "missing",
      report_expected: options.reportExpected ?? true,
      report_available: false,
      open_attempted: true,
      open_succeeded: false,
      user_action_required: true,
      recovery_category: "rerun_assessment",
    });
  }
  try {
    const opened = await options.open.openLocalFile(validated.path);
    return createReportOpeningResult({
      status: opened ? "opened" : "open_failed",
      report_expected: options.reportExpected ?? true,
      report_available: true,
      open_attempted: true,
      open_succeeded: opened,
      user_action_required: !opened,
      recovery_category: opened ? "none" : "open_report_manually",
    });
  } catch {
    return createReportOpeningResult({
      status: "open_failed",
      report_expected: options.reportExpected ?? true,
      report_available: true,
      open_attempted: true,
      open_succeeded: false,
      user_action_required: true,
      recovery_category: "open_report_manually",
    });
  }
}

export function resultForUserDeclined(): ReportOpeningResult {
  return createReportOpeningResult({
    status: "user_declined",
    report_expected: true,
    report_available: true,
    open_attempted: false,
    open_succeeded: false,
    user_action_required: false,
    recovery_category: "none",
  });
}

export function resultForMissingReport(
  reportExpected: boolean
): ReportOpeningResult {
  return createReportOpeningResult({
    status: "missing",
    report_expected: reportExpected,
    report_available: false,
    open_attempted: false,
    open_succeeded: false,
    user_action_required: true,
    recovery_category: "rerun_assessment",
  });
}

export function diagnosticsFromReportResult(
  result: ReportOpeningResult,
  operation: "open_report" | "post_assessment_report",
  primaryResultCategory: string
): ReportOpeningDiagnostics {
  return {
    report_policy_version: REPORT_OPENING_POLICY_VERSION,
    operation,
    primary_result_category: primaryResultCategory,
    report_expected: result.report_expected,
    report_available: result.report_available,
    containment_valid: result.status !== "unsafe_path",
    file_valid:
      result.report_available ||
      result.status === "opened" ||
      result.status === "open_failed" ||
      result.status === "user_declined",
    open_attempted: result.open_attempted,
    open_succeeded: result.open_succeeded,
    user_action_required: result.user_action_required,
    primary_result_preserved: true,
    telemetry_invoked: false,
    analytics_invoked: false,
    terminal_status: result.status,
    limitation_codes: result.limitations.length
      ? result.limitations
      : DEFAULT_REPORT_OPENING_LIMITATIONS,
  };
}

export function userMessageForReportResult(
  result: ReportOpeningResult
): string {
  switch (result.status) {
    case "opened":
      return "Engineering Assessment report opened.";
    case "missing":
      return "Engineering Assessment report.html not found. Run an assessment first.";
    case "unsafe_path":
      return "Report path is outside the allowed repository boundary.";
    case "invalid_file":
      return "Unable to open generated report (invalid file).";
    case "open_failed":
      return "Unable to open generated report.";
    case "user_declined":
      return "Report open skipped.";
    default:
      return "Unable to open generated report.";
  }
}
