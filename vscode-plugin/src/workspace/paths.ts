import * as path from "node:path";

/**
 * Resolve a repository-relative evidence path safely within a workspace folder.
 * Returns undefined when the path would escape the workspace.
 */
export function resolveWorkspaceRelativePath(
  workspaceFolder: string,
  relativeOrAbsolute: string
): { path: string; insideWorkspace: boolean } | undefined {
  const trimmed = relativeOrAbsolute.trim();
  if (!trimmed) {
    return undefined;
  }
  const workspaceRoot = path.resolve(workspaceFolder);
  const target = path.isAbsolute(trimmed)
    ? path.resolve(trimmed)
    : path.resolve(workspaceRoot, trimmed);
  const relative = path.relative(workspaceRoot, target);
  const insideWorkspace =
    relative === "" ||
    (!relative.startsWith("..") && !path.isAbsolute(relative));
  return { path: target, insideWorkspace };
}

export function extractEvidenceLine(excerpt?: string | null): number | undefined {
  if (!excerpt) {
    return undefined;
  }
  const match = /(?:line|L)\s*[:=]?\s*(\d+)/i.exec(excerpt);
  if (!match) {
    return undefined;
  }
  const line = Number(match[1]);
  return Number.isFinite(line) && line > 0 ? line : undefined;
}
