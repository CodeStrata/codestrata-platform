/**
 * Privacy projection for VS Code anonymous analytics (Epic 10 Slice 10.7).
 */

import { looksLikeUnsafeValue } from "../privacy";
import {
  analyticsEventToIntakeDict,
  type VsCodeAnalyticsEvent,
} from "./events";
import { VsCodeAnalyticsError } from "./errors";
import {
  COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_POLICY_VERSION,
  COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_ID,
  COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_VERSION,
} from "./runtimePolicy";
import {
  APPROVED_ANALYTICS_DURATION_BUCKETS,
  APPROVED_ANALYTICS_FAILURE_CATEGORIES,
  APPROVED_ANALYTICS_FIELD_NAMES,
  APPROVED_ANALYTICS_LIFECYCLES,
  APPROVED_ANALYTICS_OPERATION_CATEGORIES,
  APPROVED_ANALYTICS_OUTCOMES,
  APPROVED_ANALYTICS_RELEASE_ADOPTIONS,
  FORBIDDEN_ANALYTICS_FIELD_NAMES,
  VSCODE_ANALYTICS_CLIENT_NAME,
  VSCODE_ANALYTICS_EDITOR,
} from "./schema";

export type VsCodeAnalyticsProjection = {
  readonly fields: Readonly<Record<string, unknown>>;
};

const ENUM_FIELDS: Record<string, readonly string[]> = {
  client_name: [VSCODE_ANALYTICS_CLIENT_NAME],
  editor: [VSCODE_ANALYTICS_EDITOR],
  lifecycle: APPROVED_ANALYTICS_LIFECYCLES,
  operation_category: APPROVED_ANALYTICS_OPERATION_CATEGORIES,
  outcome: APPROVED_ANALYTICS_OUTCOMES,
  duration_bucket: APPROVED_ANALYTICS_DURATION_BUCKETS,
  release_adoption: APPROVED_ANALYTICS_RELEASE_ADOPTIONS,
  failure_category: APPROVED_ANALYTICS_FAILURE_CATEGORIES,
  schema_id: [COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_ID],
  schema_version: [COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_VERSION],
  policy_version: [COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_POLICY_VERSION],
  telemetry_runtime_policy_version: ["1.0"],
  telemetry_event_schema_version: ["1.0"],
};

export function projectVsCodeAnalyticsEvent(
  event: VsCodeAnalyticsEvent
): VsCodeAnalyticsProjection {
  const intake = analyticsEventToIntakeDict(event);
  const projected: Record<string, unknown> = {};

  for (const [key, value] of Object.entries(intake)) {
    if ((FORBIDDEN_ANALYTICS_FIELD_NAMES as readonly string[]).includes(key)) {
      throw new VsCodeAnalyticsError("privacy_rejected");
    }
    if (!(APPROVED_ANALYTICS_FIELD_NAMES as readonly string[]).includes(key)) {
      throw new VsCodeAnalyticsError("unknown_field");
    }
    projected[key] = normalizeValue(key, value);
  }

  const sorted: Record<string, unknown> = {};
  for (const key of Object.keys(projected).sort()) {
    sorted[key] = projected[key];
  }
  return { fields: sorted };
}

function normalizeValue(key: string, value: unknown): unknown {
  if (key === "ai_used") {
    if (typeof value !== "boolean") {
      throw new VsCodeAnalyticsError("unsafe_value");
    }
    return value;
  }
  if (key === "limitations") {
    if (!Array.isArray(value) || !value.every((item) => typeof item === "string")) {
      throw new VsCodeAnalyticsError("unsafe_value");
    }
    for (const item of value) {
      if (looksLikeUnsafeValue(item) || item.includes("/") || item.includes("\\")) {
        throw new VsCodeAnalyticsError("privacy_rejected");
      }
    }
    return [...value].sort();
  }
  if (key === "extension_version") {
    if (typeof value !== "string" || !value || value.length > 32) {
      throw new VsCodeAnalyticsError("invalid_extension_version");
    }
    if (
      looksLikeUnsafeValue(value) ||
      value.includes("/") ||
      value.includes("\\") ||
      value.includes("://")
    ) {
      throw new VsCodeAnalyticsError("privacy_rejected");
    }
    return value;
  }
  if (key in ENUM_FIELDS) {
    if (typeof value !== "string" || !ENUM_FIELDS[key].includes(value)) {
      throw new VsCodeAnalyticsError("unsafe_value");
    }
    return value;
  }
  throw new VsCodeAnalyticsError("unknown_field");
}

export function projectVsCodeAnalyticsFromMapping(
  payload: Record<string, unknown>
): VsCodeAnalyticsProjection {
  for (const key of Object.keys(payload)) {
    if ((FORBIDDEN_ANALYTICS_FIELD_NAMES as readonly string[]).includes(key)) {
      throw new VsCodeAnalyticsError("privacy_rejected");
    }
    if (!(APPROVED_ANALYTICS_FIELD_NAMES as readonly string[]).includes(key)) {
      throw new VsCodeAnalyticsError("unknown_field");
    }
  }
  const projected: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(payload)) {
    projected[key] = normalizeValue(key, value);
  }
  const sorted: Record<string, unknown> = {};
  for (const key of Object.keys(projected).sort()) {
    sorted[key] = projected[key];
  }
  return { fields: sorted };
}
