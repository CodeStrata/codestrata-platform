/**
 * Process-local VS Code analytics diagnostics (Epic 10 Slice 10.7).
 * Never includes identity, paths, payloads, or exception text.
 */

import {
  COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_POLICY_VERSION,
  COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_VERSION,
} from "./runtimePolicy";

export type VsCodeAnalyticsDiagnostics = {
  policyVersion: string;
  schemaVersion: string;
  consentDecision: string;
  attempts: number;
  projected: number;
  rejected: number;
  sunkUnavailable: number;
  sunkCaptured: number;
  operationCategory?: string;
  lifecycle?: string;
  outcome?: string;
  durationBucket?: string;
  aiUsed?: boolean;
  releaseAdoption?: string;
  limitationCodes: string[];
};

export function emptyVsCodeAnalyticsDiagnostics(
  consentDecision = "disabled_by_default"
): VsCodeAnalyticsDiagnostics {
  return {
    policyVersion: COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_POLICY_VERSION,
    schemaVersion: COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_VERSION,
    consentDecision,
    attempts: 0,
    projected: 0,
    rejected: 0,
    sunkUnavailable: 0,
    sunkCaptured: 0,
    limitationCodes: [],
  };
}

export function analyticsDiagnosticsToStableDict(
  diagnostics: VsCodeAnalyticsDiagnostics
): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    attempts: diagnostics.attempts,
    consentDecision: diagnostics.consentDecision,
    limitationCodes: [...diagnostics.limitationCodes].sort(),
    policyVersion: diagnostics.policyVersion,
    projected: diagnostics.projected,
    rejected: diagnostics.rejected,
    schemaVersion: diagnostics.schemaVersion,
    sunkCaptured: diagnostics.sunkCaptured,
    sunkUnavailable: diagnostics.sunkUnavailable,
  };
  if (diagnostics.operationCategory !== undefined) {
    payload.operationCategory = diagnostics.operationCategory;
  }
  if (diagnostics.lifecycle !== undefined) {
    payload.lifecycle = diagnostics.lifecycle;
  }
  if (diagnostics.outcome !== undefined) {
    payload.outcome = diagnostics.outcome;
  }
  if (diagnostics.durationBucket !== undefined) {
    payload.durationBucket = diagnostics.durationBucket;
  }
  if (diagnostics.aiUsed !== undefined) {
    payload.aiUsed = diagnostics.aiUsed;
  }
  if (diagnostics.releaseAdoption !== undefined) {
    payload.releaseAdoption = diagnostics.releaseAdoption;
  }
  return payload;
}
