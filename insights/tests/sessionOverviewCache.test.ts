import { afterEach, describe, expect, it, vi } from "vitest";
import {
  OVERVIEW_CACHE_TTL_MS,
  __resetOverviewCacheForTests,
  clearOverviewCache,
  isOverviewCacheFresh,
  loadOverviewWithSessionCache,
  peekOverviewCache,
  setOverviewCache,
} from "../src/api/sessionOverviewCache";
import type { MetricResult } from "../src/metrics/metricResult";

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

afterEach(() => {
  __resetOverviewCacheForTests();
});

describe("session overview cache", () => {
  it("first load fetches and stores; immediate revisit uses fresh cache", async () => {
    const fetchFresh = vi.fn(async () => [metric("total_assessments", 1)]);
    const first = await loadOverviewWithSessionCache(fetchFresh);
    expect(first.fromCache).toBe(false);
    expect(fetchFresh).toHaveBeenCalledTimes(1);
    expect(peekOverviewCache()?.metrics[0]?.value).toBe(1);

    const second = await loadOverviewWithSessionCache(fetchFresh);
    expect(second.fromCache).toBe(true);
    expect(second.background).toBeNull();
    expect(fetchFresh).toHaveBeenCalledTimes(1);
  });

  it("stale cache returns immediately and starts background refresh", async () => {
    setOverviewCache([metric("total_assessments", 2)], Date.now() - OVERVIEW_CACHE_TTL_MS - 1);
    expect(isOverviewCacheFresh()).toBe(false);

    let resolveFetch!: (v: MetricResult[]) => void;
    const fetchFresh = vi.fn(
      () =>
        new Promise<MetricResult[]>((resolve) => {
          resolveFetch = resolve;
        }),
    );

    const stale = await loadOverviewWithSessionCache(fetchFresh);
    expect(stale.fromCache).toBe(true);
    expect(stale.entry.metrics[0]?.value).toBe(2);
    expect(stale.background).not.toBeNull();
    expect(fetchFresh).toHaveBeenCalledTimes(1);

    resolveFetch([metric("total_assessments", 9)]);
    const updated = await stale.background!;
    expect(updated.metrics[0]?.value).toBe(9);
    expect(peekOverviewCache()?.metrics[0]?.value).toBe(9);
    expect(isOverviewCacheFresh()).toBe(true);
  });

  it("force bypasses freshness and replaces cache", async () => {
    setOverviewCache([metric("total_assessments", 3)], Date.now());
    const fetchFresh = vi.fn(async () => [metric("total_assessments", 4)]);
    const forced = await loadOverviewWithSessionCache(fetchFresh, { force: true });
    expect(forced.fromCache).toBe(false);
    expect(fetchFresh).toHaveBeenCalledTimes(1);
    expect(forced.entry.metrics[0]?.value).toBe(4);
  });

  it("dedupes in-flight fetches", async () => {
    let resolveFetch!: (v: MetricResult[]) => void;
    const fetchFresh = vi.fn(
      () =>
        new Promise<MetricResult[]>((resolve) => {
          resolveFetch = resolve;
        }),
    );
    const a = loadOverviewWithSessionCache(fetchFresh);
    const b = loadOverviewWithSessionCache(fetchFresh);
    expect(fetchFresh).toHaveBeenCalledTimes(1);
    resolveFetch([metric("total_assessments", 5)]);
    const [ra, rb] = await Promise.all([a, b]);
    expect(ra.entry.metrics[0]?.value).toBe(5);
    expect(rb.entry.metrics[0]?.value).toBe(5);
  });

  it("clearOverviewCache drops session memory", () => {
    setOverviewCache([metric("total_assessments", 6)]);
    clearOverviewCache();
    expect(peekOverviewCache()).toBeNull();
    expect(isOverviewCacheFresh()).toBe(false);
  });

  it("does not persist into Web Storage", async () => {
    const fetchFresh = vi.fn(async () => [metric("total_assessments", 7)]);
    await loadOverviewWithSessionCache(fetchFresh);
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
  });
});
