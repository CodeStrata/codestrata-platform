/**
 * VS Code report publish/share policy (Slice 17.21 / 18.7 journey fix).
 * Thin wrapper over Engine `codestrata report publish` — no auto-publish.
 */

export const REPORT_PUBLISH_COMMAND_ID = "codestrata.publishCurrentReport" as const;

export const REPORT_PUBLISH_POLICY = {
  policy_id: "community-vscode-report-publish-policy",
  policy_version: "1.1",
  auto_publish: false as const,
  requires_explicit_public_confirm: true as const,
  requires_telemetry_opt_in_env: false as const,
  requires_private_ack_for_local_repos: true as const,
  uses_packaged_public_community_client: true as const,
  public_reports_host: "reports.codestrata.ai",
  public_url_prefix: "https://reports.codestrata.ai/r/",
} as const;

/** User-facing confirmations (no marketing fluff). */
export const PUBLISH_CONFIRM_TITLE =
  "Publish current Assessment Report?";
export const PUBLISH_CONFIRM_DETAIL =
  "This will publish your current Assessment Report. " +
  "Anyone with the resulting link can view it. " +
  "Local reports stay on this machine. Publishing does not run automatically after assessment. " +
  "Publishing is separate from telemetry consent.";
export const PUBLISH_CONFIRM_ACTION = "Publish report";
export const PUBLISH_CANCEL_ACTION = "Cancel";

export const PRIVATE_REPO_ACK_TITLE =
  "Publish private/local Assessment Report?";
export const PRIVATE_REPO_ACK_DETAIL =
  "This report appears to come from a private/local repository. " +
  "Anyone with the resulting link can view it. " +
  "Local reports stay on this machine. Publishing is separate from telemetry consent.";
export const PRIVATE_REPO_ACK_ACTION = "Publish anyway";
