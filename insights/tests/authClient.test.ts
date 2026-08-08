import { describe, expect, it, vi } from "vitest";
import { HttpInsightsAuthClient, HttpInsightsApiClient } from "../src/api/authClient";

describe("authenticated API client", () => {
  it("sends credentials and maps 401", async () => {
    const fetchImpl = vi.fn(async () => new Response("{}", { status: 401 }));
    const client = new HttpInsightsApiClient({
      apiBaseUrl: "/api/v1",
      fetchImpl: fetchImpl as unknown as typeof fetch,
    });
    await expect(client.getOverview()).rejects.toMatchObject({ code: "unauthenticated" });
    expect(fetchImpl).toHaveBeenCalledWith(
      "/api/v1/insights/api/overview",
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("login posts password without storing token helpers", async () => {
    const fetchImpl = vi.fn(async () => new Response(JSON.stringify({ ok: true }), { status: 200 }));
    const auth = new HttpInsightsAuthClient({
      apiBaseUrl: "/api/v1",
      fetchImpl: fetchImpl as unknown as typeof fetch,
    });
    await auth.login("test-only");
    const firstCall = fetchImpl.mock.calls[0] as unknown as [string, RequestInit?];
    const init = firstCall[1] ?? {};
    expect(init.credentials).toBe("include");
    expect(String(init.body)).toContain("password");
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
  });
});
