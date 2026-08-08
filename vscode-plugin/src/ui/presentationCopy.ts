/**
 * Shared presentation copy for CodeStrata VS Code (Slice 14.5).
 *
 * Presentation only — does not change command IDs, config keys, or runtime flow.
 * Native VS Code host controls colors/themes; do not hardcode brand colors here.
 */

/** First-run activation prompt (before CLI probe). */
export const FIRST_RUN_WELCOME_MESSAGE =
  "Welcome to CodeStrata\n\nUse a local CodeStrata CLI to initialize a repository, run an assessment, and open the generated report. Optional AI uses your configured provider.";

/** CLI ready after Get Started. */
export const FIRST_RUN_ENGINE_READY_MESSAGE =
  "Welcome to CodeStrata. CodeStrata CLI is ready.\n\nInitialize this repository before running an assessment when needed, then run an assessment and open the generated report.";

/** CLI missing during onboarding. */
export const FIRST_RUN_CLI_MISSING_MESSAGE =
  "Welcome to CodeStrata\n\nCodeStrata CLI was not found. Installation is guidance-only — the extension will not install packages automatically.";

export const FIRST_RUN_ACTION_GET_STARTED = "Get Started";
export const FIRST_RUN_ACTION_LATER = "Later";
export const FIRST_RUN_ACTION_RUN_FIRST = "Run First Assessment";
export const FIRST_RUN_ACTION_ENABLE_AI = "Enable AI Enhancements…";
export const FIRST_RUN_ACTION_DISMISS = "Dismiss";
export const FIRST_RUN_ACTION_DONE = "Done";

/** Post-assessment prompt (Approach B — never auto-open). */
export const ASSESSMENT_COMPLETE_MESSAGE = "Assessment complete.";
export const ASSESSMENT_COMPLETE_OPEN_REPORT = "Open Report";
export const ASSESSMENT_COMPLETE_DISMISS = "Dismiss";

export const EMPTY_FINDINGS_LABEL = "Run your first CodeStrata assessment.";
export const EMPTY_FINDINGS_FILTERED = "No findings match the current filter.";
export const EMPTY_RECOMMENDATIONS_TITLE = "No recommendations loaded";
export const EMPTY_RECOMMENDATIONS_DESCRIPTION = "Run CodeStrata: Run Assessment";

export const STATUS_TOOLTIP_READY = "CodeStrata — Ready. Run an assessment.";
export const STATUS_TOOLTIP_RUNNING = "CodeStrata — Running assessment…";
export const STATUS_A11Y_READY = "CodeStrata ready. Activate to run an assessment.";
export const STATUS_A11Y_RUNNING = "CodeStrata assessment in progress.";
