/**
 * First-load dashboard fetch policy (Slice 20.13B).
 *
 * Auth readiness is gated by the caller. This helper only classifies transient
 * overview failures and applies at most ONE automatic retry — no sleep loops.
 */

import { AuthApiError, type AuthApiErrorCode } from "./authClient";
import type { MetricResult } from "../metrics/metricResult";

export type DashboardLoadFailureKind =
  | "AUTH_NOT_READY"
  | "UNAUTHORIZED"
  | "FORBIDDEN"
  | "NETWORK"
  | "BACKEND_UNAVAILABLE"
  | "INVALID_RESPONSE"
  | "UNKNOWN";

export function isTransientOverviewFailure(err: unknown): boolean {
  if (!(err instanceof AuthApiError)) return false;
  return err.code === "unavailable" || err.code === "network_error";
}

export function classifyOverviewFailure(err: unknown): DashboardLoadFailureKind {
  if (!(err instanceof AuthApiError)) return "UNKNOWN";
  const map: Record<AuthApiErrorCode, DashboardLoadFailureKind> = {
    unauthenticated: "UNAUTHORIZED",
    access_denied: "FORBIDDEN",
    unavailable: "BACKEND_UNAVAILABLE",
    network_error: "NETWORK",
    invalid_credentials: "UNAUTHORIZED",
    invalid_request: "INVALID_RESPONSE",
    rate_limited: "BACKEND_UNAVAILABLE",
    unknown: "UNKNOWN",
  };
  return map[err.code] ?? "UNKNOWN";
}

/**
 * Fetch overview once, with a single immediate retry for transient failures
 * on the initial load path only (`allowTransientRetry`).
 */
export async function fetchOverviewWithTransientRetry(
  fetchFresh: () => Promise<MetricResult[]>,
  options: { allowTransientRetry?: boolean } = {},
): Promise<MetricResult[]> {
  try {
    return await fetchFresh();
  } catch (err) {
    if (options.allowTransientRetry === true && isTransientOverviewFailure(err)) {
      return await fetchFresh();
    }
    throw err;
  }
}
