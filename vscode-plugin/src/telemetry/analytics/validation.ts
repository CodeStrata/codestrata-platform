/**
 * VS Code analytics validation (Epic 10 Slice 10.7).
 */

import { isAnalyticsConstructionAllowed } from "./consent";
import type { VsCodeTelemetryConsent } from "../consent";
import {
  assertVsCodeAnalyticsSchemaCompatible,
} from "./compatibility";
import {
  buildVsCodeAnalyticsEvent,
  type VsCodeAnalyticsEvent,
  type VsCodeAnalyticsInput,
} from "./events";
import { VsCodeAnalyticsError } from "./errors";
import {
  projectVsCodeAnalyticsEvent,
  type VsCodeAnalyticsProjection,
} from "./projection";
import {
  defaultVsCodeAnonymousAnalyticsPolicy,
  type VsCodeAnonymousAnalyticsPolicy,
} from "./runtimePolicy";

export function validateVsCodeAnalyticsEvent(
  event: VsCodeAnalyticsEvent,
  options?: {
    consent?: VsCodeTelemetryConsent;
    policy?: VsCodeAnonymousAnalyticsPolicy;
  }
): VsCodeAnalyticsProjection {
  const policy = options?.policy ?? defaultVsCodeAnonymousAnalyticsPolicy();
  if (policy.persistenceEnabled || policy.transmissionEnabled) {
    throw new VsCodeAnalyticsError("internal");
  }
  if (policy.installationIdentityAllowed) {
    throw new VsCodeAnalyticsError("privacy_rejected");
  }
  assertVsCodeAnalyticsSchemaCompatible(event.schemaVersion);
  if (options?.consent && !isAnalyticsConstructionAllowed(options.consent)) {
    throw new VsCodeAnalyticsError("consent_not_allowed");
  }
  // Rebuild through builders to enforce catalog consistency.
  const input: VsCodeAnalyticsInput = {
    operationCategory: event.operationCategory,
    lifecycle: event.lifecycle,
    extensionVersion: event.extensionVersion,
    releaseAdoption: event.releaseAdoption,
    aiUsed: event.aiUsed,
    outcome: event.outcome,
    durationBucket: event.durationBucket,
    failureCategory: event.failureCategory,
  };
  const rebuilt = buildVsCodeAnalyticsEvent(input);
  return projectVsCodeAnalyticsEvent(rebuilt);
}
