/** Workspace eligibility helpers (bounded categories, no path exposure). */

import type { WorkspaceKind } from "./context";

export type WorkspaceEligibilityInput = {
  readonly folderCount: number;
};

export function classifyWorkspaceKind(
  input: WorkspaceEligibilityInput
): WorkspaceKind {
  if (input.folderCount <= 0) {
    return "no_workspace";
  }
  if (input.folderCount === 1) {
    return "folder_workspace";
  }
  return "multi_root_workspace";
}

export function workspaceIsEligible(kind: WorkspaceKind): boolean {
  return kind === "folder_workspace" || kind === "multi_root_workspace";
}
