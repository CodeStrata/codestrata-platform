/** Executable / filesystem validation for explicit candidates (Slice 13.2). */

import * as fs from "node:fs";
import * as path from "node:path";

export type ExecutableValidationStatus =
  | "ok"
  | "missing"
  | "not_file"
  | "not_executable"
  | "unsafe_symlink"
  | "unsupported";

export type ExecutableValidationResult = {
  readonly status: ExecutableValidationStatus;
};

/**
 * Validate an explicit filesystem candidate.
 * Rejects directories and broken/unsafe symlink chains (max depth 4).
 * PATH bare names are not validated here (spawn+identity covers them).
 */
export function validateExplicitExecutable(
  candidatePath: string,
  options?: { readonly platform?: NodeJS.Platform }
): ExecutableValidationResult {
  const platform = options?.platform ?? process.platform;
  const trimmed = candidatePath.trim();
  if (!trimmed) {
    return { status: "missing" };
  }
  // No shell expansion / env interpolation.
  if (/[`$]/.test(trimmed) || trimmed.includes("$(") || trimmed.includes("${")) {
    return { status: "unsupported" };
  }

  let current = trimmed;
  let depth = 0;
  while (depth < 4) {
    let stat: fs.Stats;
    try {
      stat = fs.lstatSync(current);
    } catch {
      return { status: "missing" };
    }
    if (stat.isSymbolicLink()) {
      let target: string;
      try {
        target = fs.readlinkSync(current);
      } catch {
        return { status: "unsafe_symlink" };
      }
      current = path.isAbsolute(target)
        ? target
        : path.resolve(path.dirname(current), target);
      depth += 1;
      continue;
    }
    if (stat.isDirectory()) {
      return { status: "not_file" };
    }
    if (!stat.isFile()) {
      return { status: "unsupported" };
    }
    if (platform !== "win32") {
      const mode = stat.mode;
      const executable = (mode & 0o111) !== 0;
      if (!executable) {
        return { status: "not_executable" };
      }
    }
    return { status: "ok" };
  }
  return { status: "unsafe_symlink" };
}

export function isPathStyleCandidate(value: string): boolean {
  const trimmed = value.trim();
  if (!trimmed) {
    return false;
  }
  return (
    path.isAbsolute(trimmed) ||
    trimmed.includes("/") ||
    trimmed.includes("\\")
  );
}
