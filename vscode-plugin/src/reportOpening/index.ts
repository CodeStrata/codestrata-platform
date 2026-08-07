/** CodeStrata HTML report-opening contract (Slice 13.7). */

export {
  REPORT_OPENING_POLICY_ID,
  REPORT_OPENING_POLICY_VERSION,
  ENGINE_HTML_REPORT_BASENAME,
  DEFAULT_REPORT_OPENING_LIMITATIONS,
  createReportOpeningPolicy,
  reportOpeningPolicyToStableDict,
  type ReportOpeningPolicy,
} from "./policy";

export {
  REPORT_OPENING_RESULT_STATUSES,
  REPORT_RECOVERY_CATEGORIES,
  REPORT_ERROR_CATEGORIES,
  createReportOpeningResult,
  reportOpeningResultToStableDict,
  type ReportOpeningResultStatus,
  type ReportRecoveryCategory,
  type ReportOpeningResult,
  type ReportErrorCategory,
} from "./results";

export {
  reportOpeningDiagnosticsToStableDict,
  reportDiagnosticsContainForbiddenKeys,
  type ReportOpeningDiagnostics,
} from "./diagnostics";

export {
  resolveApprovedOutputRoot,
  isPathInsideRoot,
  resolveContainedPath,
  validateHtmlReportFile,
  htmlPathForRunDirectory,
  type ResolveOutputRootResult,
  type HtmlReportValidation,
} from "./containment";

export {
  locateHtmlReport,
  findLatestHtmlRunDirectory,
  openValidatedHtmlReport,
  resultForUserDeclined,
  resultForMissingReport,
  diagnosticsFromReportResult,
  userMessageForReportResult,
  type LocateReportInput,
  type LocateReportOutcome,
  type OpenHtmlAdapter,
} from "./orchestration";
