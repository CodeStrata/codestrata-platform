/**
 * Path containment and HTML report file validation (Slice 13.7).
 */

import * as fs from "node:fs";
import * as path from "node:path";

import { ENGINE_HTML_REPORT_BASENAME } from "./policy";

export type ResolveOutputRootResult = {
  readonly outputRoot: string;
  /** Absolute output outside the repository is rejected for Community open. */
  readonly contained: boolean;
};

/**
 * Resolve approved Engine output root. Relative paths join workspace.
 * Absolute output that escapes the repository is rejected (containment).
 */
export function resolveApprovedOutputRoot(
  workspaceRoot: string,
  outputDirectory: string
): ResolveOutputRootResult {
  const workspace = path.resolve(workspaceRoot);
  const trimmed = (outputDirectory || "reports").trim() || "reports";
  const outputRoot = path.isAbsolute(trimmed)
    ? path.resolve(trimmed)
    : path.resolve(workspace, trimmed);
  const relative = path.relative(workspace, outputRoot);
  const contained =
    relative === "" ||
    (!relative.startsWith("..") && !path.isAbsolute(relative));
  return { outputRoot, contained };
}

export function isPathInsideRoot(root: string, candidate: string): boolean {
  const resolvedRoot = path.resolve(root);
  const resolvedCandidate = path.resolve(candidate);
  const relative = path.relative(resolvedRoot, resolvedCandidate);
  return (
    relative === "" ||
    (!relative.startsWith("..") && !path.isAbsolute(relative))
  );
}

/**
 * Resolve realpath when available; fall back to path.resolve.
 * Rejects when the resolved path escapes the approved root.
 */
export function resolveContainedPath(
  approvedRoot: string,
  candidate: string
): { readonly path: string; readonly contained: boolean } {
  const rootResolved = path.resolve(approvedRoot);
  let candidateResolved = path.resolve(candidate);
  try {
    if (fs.existsSync(rootResolved)) {
      // realpathSync follows symlinks — use for escape detection.
      const rootReal = fs.realpathSync(rootResolved);
      if (fs.existsSync(candidateResolved)) {
        candidateResolved = fs.realpathSync(candidateResolved);
      }
      return {
        path: candidateResolved,
        contained: isPathInsideRoot(rootReal, candidateResolved),
      };
    }
  } catch {
    // Fall through to non-realpath containment.
  }
  return {
    path: candidateResolved,
    contained: isPathInsideRoot(rootResolved, candidateResolved),
  };
}

export type HtmlReportValidation =
  | { readonly ok: true; readonly path: string }
  | {
      readonly ok: false;
      readonly reason:
        | "missing"
        | "unsafe_path"
        | "not_regular_file"
        | "type_invalid"
        | "symlink_escape";
    };

/**
 * Validate a candidate HTML report path for local opening.
 * Does not read file contents.
 */
export function validateHtmlReportFile(options: {
  readonly workspaceRoot: string;
  readonly outputDirectory: string;
  readonly candidatePath: string | undefined;
}): HtmlReportValidation {
  if (!options.candidatePath) {
    return { ok: false, reason: "missing" };
  }
  const output = resolveApprovedOutputRoot(
    options.workspaceRoot,
    options.outputDirectory
  );
  if (!output.contained) {
    return { ok: false, reason: "unsafe_path" };
  }
  // Candidate must remain inside repository AND inside approved output root.
  const inWorkspace = resolveContainedPath(
    options.workspaceRoot,
    options.candidatePath
  );
  if (!inWorkspace.contained) {
    return { ok: false, reason: "unsafe_path" };
  }
  const inOutput = resolveContainedPath(output.outputRoot, options.candidatePath);
  if (!inOutput.contained) {
    return { ok: false, reason: "unsafe_path" };
  }
  const target = inOutput.path;
  try {
    // lstat detects symlink at the leaf before following.
    const lstat = fs.lstatSync(target);
    if (lstat.isSymbolicLink()) {
      const real = resolveContainedPath(output.outputRoot, target);
      if (!real.contained) {
        return { ok: false, reason: "symlink_escape" };
      }
    }
    const stat = fs.statSync(target);
    if (!stat.isFile()) {
      return { ok: false, reason: "not_regular_file" };
    }
  } catch {
    return { ok: false, reason: "missing" };
  }
  const base = path.basename(target).toLowerCase();
  if (base !== ENGINE_HTML_REPORT_BASENAME) {
    return { ok: false, reason: "type_invalid" };
  }
  return { ok: true, path: target };
}

export function htmlPathForRunDirectory(runDirectory: string): string {
  return path.join(runDirectory, ENGINE_HTML_REPORT_BASENAME);
}
