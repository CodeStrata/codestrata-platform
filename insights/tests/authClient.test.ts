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
      expect.stringMatching(/^\/api\/v1\/insights\/api\/overview\?_=\d+$/),
      expect.objectContaining({
        credentials: "include",
        cache: "no-store",
      }),
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

  it("maps wrong password to invalid_credentials and 429 to rate_limited", async () => {
    const wrong = vi.fn(
      async () =>
        new Response(JSON.stringify({ error: { code: "invalid_credentials", message: "Invalid password" } }), {
          status: 401,
        }),
    );
    const authWrong = new HttpInsightsAuthClient({
      apiBaseUrl: "/api/v1",
      fetchImpl: wrong as unknown as typeof fetch,
    });
    await expect(authWrong.login("nope")).rejects.toMatchObject({ code: "invalid_credentials" });

    const limited = vi.fn(
      async () =>
        new Response(JSON.stringify({ error: { code: "rate_limited", message: "Too many requests" } }), {
          status: 429,
        }),
    );
    const authLimited = new HttpInsightsAuthClient({
      apiBaseUrl: "/api/v1",
      fetchImpl: limited as unknown as typeof fetch,
    });
    await expect(authLimited.login("nope")).rejects.toMatchObject({ code: "rate_limited" });
  });

  it("maps empty/invalid schema 422 to invalid_request and fetch throw to network_error", async () => {
    const schema = vi.fn(
      async () =>
        new Response(
          JSON.stringify({ error: { code: "invalid_request_schema", message: "Request payload failed validation." } }),
          { status: 422 },
        ),
    );
    const authSchema = new HttpInsightsAuthClient({
      apiBaseUrl: "/api/v1",
      fetchImpl: schema as unknown as typeof fetch,
    });
    await expect(authSchema.login("")).rejects.toMatchObject({ code: "invalid_request" });

    const boom = vi.fn(async () => {
      throw new TypeError("Failed to fetch");
    });
    const authNet = new HttpInsightsAuthClient({
      apiBaseUrl: "/api/v1",
      fetchImpl: boom as unknown as typeof fetch,
    });
    await expect(authNet.login("x")).rejects.toMatchObject({ code: "network_error" });

    const overviewNet = new HttpInsightsApiClient({
      apiBaseUrl: "/api/v1",
      fetchImpl: boom as unknown as typeof fetch,
    });
    await expect(overviewNet.getOverview()).rejects.toMatchObject({ code: "network_error" });
  });

  it("calls global fetch without illegal-invocation detachment", async () => {
    const calls: unknown[] = [];
    const bound = globalThis.fetch;
    const spy = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      calls.push({ input, init, thisIsWindow: true });
      return new Response(JSON.stringify({ error: { code: "invalid_credentials" } }), { status: 401 });
    });
    try {
      const auth = new HttpInsightsAuthClient({ apiBaseUrl: "/api/v1" });
      await expect(auth.login("x")).rejects.toMatchObject({ code: "invalid_credentials" });
      expect(spy).toHaveBeenCalled();
      expect(String(spy.mock.calls[0]?.[0])).toContain("/insights/auth/login");
    } finally {
      spy.mockRestore();
      // ensure we did not leave fetch broken
      expect(globalThis.fetch).toBe(bound);
    }
  });
});
