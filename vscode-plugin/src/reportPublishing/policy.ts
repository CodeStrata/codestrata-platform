/**
 * VS Code report publish/share policy (Slice 17.21).
 * Thin wrapper over Engine `codestrata report publish` — no auto-publish.
 */

export const REPORT_PUBLISH_COMMAND_ID = "codestrata.publishCurrentReport" as const;

export const REPORT_PUBLISH_POLICY = {
  policy_id: "community-vscode-report-publish-policy",
  policy_version: "1.0",
  auto_publish: false as const,
  requires_explicit_public_confirm: true as const,
  requires_telemetry_opt_in_env: true as const,
  requires_private_ack_for_local_repos: true as const,
  public_reports_host: "reports.codestrata.ai",
  public_url_prefix: "https://reports.codestrata.ai/r/",
} as const;

/** User-facing confirmations (no marketing fluff). */
export const PUBLISH_CONFIRM_TITLE =
  "Publish current CodeStrata report publicly?";
export const PUBLISH_CONFIRM_DETAIL =
  "This uploads the current local assessment HTML to a branded public URL. " +
  "Local reports stay on this machine. Publishing does not run automatically after assessment.";
export const PUBLISH_CONFIRM_ACTION = "Publish publicly";
export const PUBLISH_CANCEL_ACTION = "Cancel";

export const PRIVATE_REPO_ACK_TITLE =
  "This assessment looks private/local";
export const PRIVATE_REPO_ACK_DETAIL =
  "Repository id starts with local-. Confirm you intend to publish a public link " +
  "for this assessment.";
export const PRIVATE_REPO_ACK_ACTION = "Acknowledge and publish";

export const TELEMETRY_PUBLISH_TITLE =
  "Cloud publishing requires telemetry participation";
export const TELEMETRY_PUBLISH_DETAIL =
  "CodeStrata will set temporary process eligibility for this publish only " +
  "(CODESTRATA_TELEMETRY_OPT_IN). Assessment telemetry consent is separate and " +
  "still defaults off. Continue?";
export const TELEMETRY_PUBLISH_ACTION = "Allow for this publish";
