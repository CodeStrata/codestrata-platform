/**
 * Bounded VS Code analytics error codes (Epic 10 Slice 10.7).
 * Never carries rejected values or exception text.
 */

export type VsCodeAnalyticsErrorCode =
  | "invalid_operation_category"
  | "invalid_extension_version"
  | "invalid_release_adoption"
  | "invalid_lifecycle"
  | "invalid_outcome"
  | "invalid_failure_category"
  | "invalid_duration_bucket"
  | "outcome_failure_mismatch"
  | "privacy_rejected"
  | "consent_not_allowed"
  | "incompatible_schema"
  | "unknown_field"
  | "unsafe_value"
  | "internal";

export class VsCodeAnalyticsError extends Error {
  readonly code: VsCodeAnalyticsErrorCode;

  constructor(code: VsCodeAnalyticsErrorCode) {
    super(code);
    this.code = code;
    this.name = "VsCodeAnalyticsError";
  }
}
