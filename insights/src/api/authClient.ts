/** Auth and Insights API transport — credentials via HttpOnly cookie only. */

import type { MetricId, MetricResult } from "../metrics/metricResult";
import {
  unavailableResult,
  type InsightsApiClient,
  type PublishedReportsRegistry,
  type ValidationReportsPage,
} from "./insightsApi";

export type AuthApiErrorCode =
  | "unauthenticated"
  | "access_denied"
  | "unavailable"
  | "invalid_credentials"
  | "invalid_request"
  | "rate_limited"
  | "network_error"
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
  if (status === 429) return "rate_limited";
  if (status >= 500) return "unavailable";
  return "unknown";
}

function mapLoginFailure(res: Response, body: unknown): AuthApiError {
  const envelope = body as { error?: { code?: string; message?: string } } | null;
  const code = envelope?.error?.code;
  if (res.status === 401 || code === "invalid_credentials") {
    return new AuthApiError("invalid_credentials", res.status, "Invalid password");
  }
  if (res.status === 429 || code === "rate_limited") {
    return new AuthApiError("rate_limited", res.status, "Too many requests");
  }
  if (res.status === 403 || code === "invalid_origin" || code === "authorization_denied") {
    return new AuthApiError("access_denied", res.status, "Request blocked");
  }
  if (res.status === 422 || code === "invalid_request_schema") {
    return new AuthApiError("invalid_request", res.status, "Invalid request");
  }
  if (res.status === 415 || code === "unsupported_media_type") {
    return new AuthApiError("invalid_request", res.status, "Invalid request");
  }
  if (
    res.status === 503 ||
    code === "auth_service_unavailable" ||
    code === "authentication_unavailable"
  ) {
    return new AuthApiError("unavailable", res.status, "Authentication unavailable");
  }
  if (res.status >= 500) {
    return new AuthApiError("unavailable", res.status, "Authentication unavailable");
  }
  return new AuthApiError(mapStatus(res.status), res.status, "Authentication unavailable");
}

export class HttpInsightsAuthClient implements InsightsAuthClient {
  constructor(private readonly config: InsightsApiConfig) {}

  private fetchFn(
    input: RequestInfo | URL,
    init?: RequestInit,
  ): Promise<Response> {
    // Never call a detached `fetch` reference — Chrome throws
    // "Illegal invocation" which surfaced as a generic network error.
    const impl = this.config.fetchImpl;
    if (impl) return impl(input, init);
    return globalThis.fetch(input, init);
  }

  async login(password: string): Promise<void> {
    let res: Response;
    try {
      res = await this.fetchFn(joinUrl(this.config.apiBaseUrl, "/insights/auth/login"), {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ password }),
      });
    } catch (err) {
      const name = err instanceof Error ? err.name : "";
      const message = err instanceof Error ? err.message : "";
      if (name === "AbortError") {
        throw new AuthApiError("network_error", 0, "Request aborted");
      }
      // Keep message generic in UI; log safe diagnostics for owner DevTools.
      console.warn("[codestrata-insights] login fetch failed", name, message.slice(0, 80));
      throw new AuthApiError("network_error", 0, "Network error");
    }
    if (res.ok) return;
    const body = await parseJson(res);
    throw mapLoginFailure(res, body);
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

  private fetchFn(
    input: RequestInfo | URL,
    init?: RequestInit,
  ): Promise<Response> {
    const impl = this.config.fetchImpl;
    if (impl) return impl(input, init);
    return globalThis.fetch(input, init);
  }

  async getOverview(): Promise<MetricResult[]> {
    const url = joinUrl(this.config.apiBaseUrl, "/insights/api/overview");
    let res: Response;
    try {
      res = await this.fetchFn(`${url}?_=${Date.now()}`, {
        method: "GET",
        credentials: "include",
        cache: "no-store",
        headers: {
          Accept: "application/json",
          "Cache-Control": "no-cache",
        },
      });
    } catch (err) {
      const name = err instanceof Error ? err.name : "";
      if (name === "AbortError") {
        throw new AuthApiError("network_error", 0, "Request aborted");
      }
      throw new AuthApiError("network_error", 0, "Network error");
    }
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

  async getPublishedReports(): Promise<PublishedReportsRegistry> {
    const res = await this.fetchFn(
      joinUrl(this.config.apiBaseUrl, "/insights/api/published-reports"),
      {
        method: "GET",
        credentials: "include",
        headers: { Accept: "application/json" },
      },
    );
    if (res.status === 401) {
      throw new AuthApiError("unauthenticated", 401, "Authentication required");
    }
    if (res.status === 403) {
      throw new AuthApiError("access_denied", 403, "Access denied");
    }
    if (!res.ok) {
      throw new AuthApiError(mapStatus(res.status), res.status, "Published reports unavailable");
    }
    const body = (await parseJson(res)) as PublishedReportsRegistry | null;
    return {
      assessments: Array.isArray(body?.assessments) ? body!.assessments : [],
      engineering_intelligence: Array.isArray(body?.engineering_intelligence)
        ? body!.engineering_intelligence
        : [],
      source: body?.source,
      note: body?.note,
    };
  }

  async getValidationReports(opts?: {
    limit?: number;
    cursor?: string;
  }): Promise<ValidationReportsPage> {
    const params = new URLSearchParams();
    if (opts?.limit != null) params.set("limit", String(opts.limit));
    if (opts?.cursor) params.set("cursor", opts.cursor);
    const qs = params.toString();
    const path =
      "/insights/api/validation-reports" + (qs ? `?${qs}` : "");
    const res = await this.fetchFn(joinUrl(this.config.apiBaseUrl, path), {
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
      throw new AuthApiError(mapStatus(res.status), res.status, "Validation reports unavailable");
    }
    const body = (await parseJson(res)) as ValidationReportsPage | null;
    return {
      items: Array.isArray(body?.items) ? body!.items : [],
      next_cursor: body?.next_cursor ?? null,
      limit: typeof body?.limit === "number" ? body.limit : opts?.limit ?? 50,
      temporary: body?.temporary ?? true,
      purpose: body?.purpose,
      note: body?.note,
      source: body?.source,
    };
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
