/**
 * INSIGHTS-FIRSTLOAD-01…07 — first authenticated dashboard load reliability.
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { App } from "../src/app/App";
import { AuthApiError, type InsightsAuthClient } from "../src/api/authClient";
import type { InsightsApiClient } from "../src/api/insightsApi";
import type { MetricResult } from "../src/metrics/metricResult";
import { SYNTHETIC_MOCK_RESULTS } from "../src/api/syntheticMocks";
import { V02_OVERVIEW_METRIC_IDS } from "../src/dashboard/labels";
import {
  __resetOverviewCacheForTests,
  peekOverviewCache,
} from "../src/api/sessionOverviewCache";
import {
  classifyOverviewFailure,
  fetchOverviewWithTransientRetry,
  isTransientOverviewFailure,
} from "../src/api/firstLoadOverview";

function metric(id: string, value: number): MetricResult {
  return {
    metric_id: id,
    status: "ok",
    window: {
      start_date_utc: "2026-01-01",
      end_date_utc: "2026-01-31",
      horizon: "bounded_period",
    },
    value,
    groups: [],
    completeness: "complete",
    denominator: null,
    share: null,
    limitations: [],
  };
}

function overviewNine(): MetricResult[] {
  return V02_OVERVIEW_METRIC_IDS.map((id, i) => metric(id, i + 1));
}

class ControllableAuth implements InsightsAuthClient {
  authenticated = false;
  sessionGate: Promise<void> | null = null;
  loginCalls = 0;

  async login(_password: string): Promise<void> {
    this.loginCalls += 1;
    this.authenticated = true;
  }

  async logout(): Promise<void> {
    this.authenticated = false;
  }

  async getSession(): Promise<{ authenticated: boolean }> {
    if (this.sessionGate) await this.sessionGate;
    return { authenticated: this.authenticated };
  }
}

function mockApi(getOverview: () => Promise<MetricResult[]>): InsightsApiClient {
  return {
    getOverview,
    getMetric: async (id) =>
      (await getOverview()).find((m) => m.metric_id === id) ?? metric(String(id), 0),
    getPublishedReports: async () => ({ assessments: [], engineering_intelligence: [] }),
    getValidationReports: async () => ({
      items: [],
      next_cursor: null,
      limit: 50,
      temporary: true,
    }),
  };
}

async function flush(): Promise<void> {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
  });
}

describe("INSIGHTS-FIRSTLOAD first-load reliability", () => {
  let root: Root | null = null;
  let host: HTMLDivElement | null = null;

  function mount(auth: InsightsAuthClient, api: InsightsApiClient): HTMLDivElement {
    host = document.createElement("div");
    document.body.appendChild(host);
    root = createRoot(host);
    act(() => {
      root!.render(<App authClient={auth} apiClient={api} />);
    });
    return host;
  }

  afterEach(() => {
    __resetOverviewCacheForTests();
    if (root && host) {
      act(() => {
        root!.unmount();
      });
      host.remove();
    }
    root = null;
    host = null;
  });

  it("INSIGHTS-FIRSTLOAD-01: session initially loading → dashboard fetch NOT called", async () => {
    let resolveSession!: () => void;
    const gate = new Promise<void>((r) => {
      resolveSession = r;
    });
    const auth = new ControllableAuth();
    auth.authenticated = true;
    auth.sessionGate = gate;
    const getOverview = vi.fn(async () => overviewNine());
    mount(auth, mockApi(getOverview));

    expect(host!.textContent).toContain("Checking session");
    expect(getOverview).not.toHaveBeenCalled();

    await act(async () => {
      resolveSession();
      await flush();
    });
    await flush();
    expect(getOverview).toHaveBeenCalled();
  });

  it("INSIGHTS-FIRSTLOAD-02: session becomes authenticated → dashboard fetch called exactly once", async () => {
    const auth = new ControllableAuth();
    auth.authenticated = true;
    const getOverview = vi.fn(async () => overviewNine());
    mount(auth, mockApi(getOverview));
    await flush();
    await flush();
    expect(getOverview).toHaveBeenCalledTimes(1);
  });

  it("INSIGHTS-FIRSTLOAD-03: successful first authenticated request → dashboard renders; unavailable never shown", async () => {
    const auth = new ControllableAuth();
    auth.authenticated = true;
    const getOverview = vi.fn(async () => overviewNine());
    mount(auth, mockApi(getOverview));
    await flush();
    await flush();
    expect(host!.textContent).toContain("Total Assessments");
    expect(host!.textContent).not.toContain("Dashboard unavailable");
    expect(host!.querySelector('[data-testid="dashboard-loading"]')).toBeNull();
    expect(peekOverviewCache()?.metrics).toHaveLength(9);
  });

  it("INSIGHTS-FIRSTLOAD-04: real backend failure after auth ready → unavailable + Retry", async () => {
    const auth = new ControllableAuth();
    auth.authenticated = true;
    const getOverview = vi.fn(async () => {
      throw new AuthApiError("unavailable", 503, "Insights unavailable");
    });
    mount(auth, mockApi(getOverview));
    await flush();
    await flush();
    expect(host!.textContent).toContain("Dashboard unavailable");
    expect(host!.textContent).toContain("Retry");
    // Initial attempt + one automatic transient retry.
    expect(getOverview.mock.calls.length).toBe(2);
  });

  it("INSIGHTS-FIRSTLOAD-05: Retry after real transient failure → dashboard renders", async () => {
    const auth = new ControllableAuth();
    auth.authenticated = true;
    let calls = 0;
    const getOverview = vi.fn(async () => {
      calls += 1;
      if (calls <= 2) {
        throw new AuthApiError("unavailable", 503, "Insights unavailable");
      }
      return overviewNine();
    });
    mount(auth, mockApi(getOverview));
    await flush();
    await flush();
    expect(host!.textContent).toContain("Dashboard unavailable");

    const retry = Array.from(host!.querySelectorAll("button")).find(
      (b) => b.textContent === "Retry",
    );
    expect(retry).toBeTruthy();
    await act(async () => {
      retry!.dispatchEvent(new MouseEvent("click", { bubbles: true }));
      await flush();
    });
    await flush();
    expect(host!.textContent).not.toContain("Dashboard unavailable");
    expect(host!.textContent).toContain("Total Assessments");
  });

  it("INSIGHTS-FIRSTLOAD-06: 401/403 handling does not leak token/session details", async () => {
    const denied = new AuthApiError("access_denied", 403, "cookie=secret; Bearer abc");
    expect(classifyOverviewFailure(denied)).toBe("FORBIDDEN");
    const unauth = new AuthApiError("unauthenticated", 401, "session_token=xyz");
    expect(classifyOverviewFailure(unauth)).toBe("UNAUTHORIZED");

    const auth = new ControllableAuth();
    auth.authenticated = true;
    const getOverview = vi.fn(async () => {
      throw denied;
    });
    mount(auth, mockApi(getOverview));
    await flush();
    await flush();
    const text = host!.textContent ?? "";
    expect(text).toContain("Access denied");
    expect(text).not.toContain("cookie=");
    expect(text).not.toContain("Bearer");
    expect(text).not.toContain("session_token");
  });

  it("INSIGHTS-FIRSTLOAD-07: existing metric values/count semantics unchanged", () => {
    expect(V02_OVERVIEW_METRIC_IDS).toHaveLength(9);
    expect(new Set(V02_OVERVIEW_METRIC_IDS)).toEqual(
      new Set([
        "total_assessments",
        "first_assessments",
        "repeat_assessments",
        "successful_assessments",
        "failed_assessments",
        "published_reports",
        "github_stars",
        "github_forks",
        "community_sentiment",
      ]),
    );
    const ids = SYNTHETIC_MOCK_RESULTS.map((r) => r.metric_id);
    for (const id of V02_OVERVIEW_METRIC_IDS) {
      expect(ids).toContain(id);
    }
  });

  it("retries once for unavailable / network_error only", async () => {
    const failOnce = vi
      .fn()
      .mockRejectedValueOnce(new AuthApiError("unavailable", 503, "x"))
      .mockResolvedValueOnce([metric("total_assessments", 1)]);
    const ok = await fetchOverviewWithTransientRetry(failOnce, {
      allowTransientRetry: true,
    });
    expect(ok).toHaveLength(1);
    expect(failOnce).toHaveBeenCalledTimes(2);

    const forbidden = vi
      .fn()
      .mockRejectedValue(new AuthApiError("access_denied", 403, "no"));
    await expect(
      fetchOverviewWithTransientRetry(forbidden, { allowTransientRetry: true }),
    ).rejects.toMatchObject({ code: "access_denied" });
    expect(forbidden).toHaveBeenCalledTimes(1);

    expect(isTransientOverviewFailure(new AuthApiError("unavailable", 503, ""))).toBe(
      true,
    );
    expect(isTransientOverviewFailure(new AuthApiError("unauthenticated", 401, ""))).toBe(
      false,
    );
  });

  it("login confirms session before authenticated state (cookie readiness)", async () => {
    const auth = new ControllableAuth();
    auth.authenticated = false;
    auth.login = async () => {
      // Login HTTP succeeds but session cookie is not yet readable.
      auth.authenticated = false;
    };

    const getOverview = vi.fn(async () => overviewNine());
    mount(auth, mockApi(getOverview));
    await flush();

    const password = host!.querySelector('input[type="password"]') as HTMLInputElement;
    const form = host!.querySelector("form") as HTMLFormElement;
    await act(async () => {
      password.value = "owner-password";
      form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
      await flush();
    });
    await flush();
    expect(getOverview).not.toHaveBeenCalled();
    expect(host!.textContent).toMatch(/Sign-in failed/i);
  });
});
