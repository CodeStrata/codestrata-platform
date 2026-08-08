/** Auth and Insights API transport — credentials via HttpOnly cookie only. */

import type { MetricId, MetricResult } from "../metrics/metricResult";
import { unavailableResult, type InsightsApiClient } from "./insightsApi";

export type AuthApiErrorCode =
  | "unauthenticated"
  | "access_denied"
  | "unavailable"
  | "invalid_credentials"
  | "unknown";

export class AuthApiError extends Error {
  readonly code: AuthApiErrorCode;
  readonly status: number;

  constructor(code: AuthApiErrorCode, status: number, message: string) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

export interface InsightsAuthClient {
  login(password: string): Promise<void>;
  logout(): Promise<void>;
  getSession(): Promise<{ authenticated: boolean }>;
}

export interface InsightsApiConfig {
  /** Absolute API root including /api/v1, e.g. "" for same-origin proxy or http://localhost:8000/api/v1 */
  apiBaseUrl: string;
  /** Extra origins never stored; fetch always credentials:include */
  fetchImpl?: typeof fetch;
}

function joinUrl(base: string, path: string): string {
  const b = base.replace(/\/$/, "");
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${b}${p}`;
}

async function parseJson(res: Response): Promise<unknown> {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

function mapStatus(status: number): AuthApiErrorCode {
  if (status === 401) return "unauthenticated";
  if (status === 403) return "access_denied";
  if (status >= 500) return "unavailable";
  return "unknown";
}

export class HttpInsightsAuthClient implements InsightsAuthClient {
  constructor(private readonly config: InsightsApiConfig) {}

  private get fetchFn(): typeof fetch {
    return this.config.fetchImpl ?? fetch;
  }

  async login(password: string): Promise<void> {
    const res = await this.fetchFn(joinUrl(this.config.apiBaseUrl, "/insights/auth/login"), {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ password }),
    });
    if (res.ok) return;
    if (res.status === 401) {
      throw new AuthApiError("invalid_credentials", 401, "Invalid password");
    }
    throw new AuthApiError(mapStatus(res.status), res.status, "Authentication unavailable");
  }

  async logout(): Promise<void> {
    await this.fetchFn(joinUrl(this.config.apiBaseUrl, "/insights/auth/logout"), {
      method: "POST",
      credentials: "include",
      headers: { Accept: "application/json" },
    });
  }

  async getSession(): Promise<{ authenticated: boolean }> {
    const res = await this.fetchFn(joinUrl(this.config.apiBaseUrl, "/insights/auth/session"), {
      method: "GET",
      credentials: "include",
      headers: { Accept: "application/json" },
    });
    if (!res.ok) {
      return { authenticated: false };
    }
    const body = (await parseJson(res)) as { authenticated?: boolean } | null;
    return { authenticated: Boolean(body?.authenticated) };
  }
}

export class HttpInsightsApiClient implements InsightsApiClient {
  constructor(private readonly config: InsightsApiConfig) {}

  private get fetchFn(): typeof fetch {
    return this.config.fetchImpl ?? fetch;
  }

  async getOverview(): Promise<MetricResult[]> {
    const res = await this.fetchFn(joinUrl(this.config.apiBaseUrl, "/insights/api/overview"), {
      method: "GET",
      credentials: "include",
      headers: { Accept: "application/json" },
    });
    if (res.status === 401) {
      throw new AuthApiError("unauthenticated", 401, "Authentication required");
    }
    if (res.status === 403) {
      throw new AuthApiError("access_denied", 403, "Access denied");
    }
    if (!res.ok) {
      throw new AuthApiError(mapStatus(res.status), res.status, "Insights unavailable");
    }
    const body = (await parseJson(res)) as { metrics?: MetricResult[] } | null;
    return Array.isArray(body?.metrics) ? body!.metrics! : [];
  }

  async getMetric(metricId: MetricId | string): Promise<MetricResult> {
    const overview = await this.getOverview();
    return overview.find((m) => m.metric_id === metricId) ?? unavailableResult(metricId);
  }
}

/** Resolve API base from Vite env; production default is same-origin /api/v1. */
export function resolveInsightsApiBaseUrl(
  env: ImportMetaEnv | Record<string, string | undefined> = import.meta.env,
): string {
  const raw = (env.VITE_INSIGHTS_API_BASE_URL as string | undefined)?.trim();
  if (raw) return raw.replace(/\/$/, "");
  return "/api/v1";
}

export { UnavailableInsightsApiClient, MockInsightsApiClient } from "./insightsApi";
