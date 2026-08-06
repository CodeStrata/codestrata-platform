/**
 * Privacy helpers for VS Code telemetry (Slice 9.13).
 */

import { APPROVED_FIELD_NAMES } from "./events";

const FORBIDDEN_NAME_FRAGMENTS = [
  "workspace",
  "repository",
  "document",
  "path",
  "finding",
  "evidence",
  "prompt",
  "response",
  "credential",
  "password",
  "token",
  "secret",
  "api_key",
  "installation",
  "machine",
  "argv",
  "model",
  "provider",
  "cost",
] as const;

const UNSAFE_VALUE_RE =
  /(\/Users\/|\/home\/|[A-Za-z]:\\|https?:\/\/|file:\/\/|-----BEGIN|password=|secret=)/i;

export function isApprovedFieldName(name: string): boolean {
  return (APPROVED_FIELD_NAMES as readonly string[]).includes(name);
}

export function isForbiddenFieldName(name: string): boolean {
  const lower = name.toLowerCase();
  if ((APPROVED_FIELD_NAMES as readonly string[]).includes(lower)) {
    return false;
  }
  return FORBIDDEN_NAME_FRAGMENTS.some((frag) => lower.includes(frag));
}

export function looksLikeUnsafeValue(value: unknown): boolean {
  if (typeof value !== "string") {
    return false;
  }
  if (value.includes("\n") || value.includes("\r")) {
    return true;
  }
  if (value.length > 64) {
    return true;
  }
  return UNSAFE_VALUE_RE.test(value);
}

export function assertNoForbiddenKeys(payload: Record<string, unknown>): void {
  for (const key of Object.keys(payload)) {
    if (!isApprovedFieldName(key) || isForbiddenFieldName(key)) {
      throw new Error("unknown_or_forbidden_field");
    }
  }
}
