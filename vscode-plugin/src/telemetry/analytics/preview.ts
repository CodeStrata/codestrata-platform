/**
 * Local analytics preview (Epic 10 Slice 10.7).
 * No consent required for illustrative preview. No transport. No identity.
 */

import {
  buildVsCodeAnalyticsEvent,
  type VsCodeAnalyticsEvent,
} from "./events";
import {
  projectVsCodeAnalyticsEvent,
  type VsCodeAnalyticsProjection,
} from "./projection";
import {
  COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_POLICY_VERSION,
  COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_VERSION,
} from "./runtimePolicy";

export type VsCodeAnalyticsPreview = {
  readonly schemaVersion: string;
  readonly policyVersion: string;
  readonly transmissionPerformed: false;
  readonly persistencePerformed: false;
  readonly localOnly: true;
  readonly identityPresent: false;
  readonly event: VsCodeAnalyticsProjection;
};

export function buildVsCodeAnalyticsPreview(options?: {
  event?: VsCodeAnalyticsEvent;
  extensionVersion?: string;
}): VsCodeAnalyticsPreview {
  const event =
    options?.event ??
    buildVsCodeAnalyticsEvent({
      operationCategory: "assess",
      lifecycle: "feature_invoked",
      extensionVersion: options?.extensionVersion ?? "0.2.0",
      releaseAdoption: "development",
      aiUsed: false,
    });
  const projected = projectVsCodeAnalyticsEvent(event);
  return {
    schemaVersion: COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_VERSION,
    policyVersion: COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_POLICY_VERSION,
    transmissionPerformed: false,
    persistencePerformed: false,
    localOnly: true,
    identityPresent: false,
    event: projected,
  };
}

export function analyticsPreviewToStableJson(
  preview: VsCodeAnalyticsPreview
): string {
  const payload = {
    event: preview.event.fields,
    identityPresent: preview.identityPresent,
    localOnly: preview.localOnly,
    persistencePerformed: preview.persistencePerformed,
    policyVersion: preview.policyVersion,
    schemaVersion: preview.schemaVersion,
    transmissionPerformed: preview.transmissionPerformed,
  };
  return JSON.stringify(payload, Object.keys(payload).sort());
}
