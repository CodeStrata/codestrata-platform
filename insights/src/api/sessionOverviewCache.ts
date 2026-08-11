/**
 * Session-scoped Insights overview cache (Slice 19.5).
 *
 * In-memory only — not sessionStorage/localStorage, not cross-user.
 * Cleared on logout / session invalidation. HTTP transport remains no-store;
 * this only avoids identical client re-fetches during short navigation windows.
 */

import type { MetricResult } from "../metrics/metricResult";

/** Soft freshness window before a silent background refresh. */
export const OVERVIEW_CACHE_TTL_MS = 45_000;

export interface OverviewCacheEntry {
  readonly metrics: MetricResult[];
  /** Epoch ms of the successful fetch that produced these metrics. */
  readonly fetchedAt: number;
}

let entry: OverviewCacheEntry | null = null;
let inflight: Promise<OverviewCacheEntry> | null = null;

export function peekOverviewCache(): OverviewCacheEntry | null {
  return entry;
}

export function isOverviewCacheFresh(
  cached: OverviewCacheEntry | null = entry,
  now: number = Date.now(),
): boolean {
  return cached != null && now - cached.fetchedAt < OVERVIEW_CACHE_TTL_MS;
}

export function setOverviewCache(
  metrics: MetricResult[],
  fetchedAt: number = Date.now(),
): OverviewCacheEntry {
  entry = { metrics, fetchedAt };
  return entry;
}

export function clearOverviewCache(): void {
  entry = null;
  inflight = null;
}

/**
 * Fetch overview with session cache semantics.
 *
 * - force: always hit the network (manual Refresh / Retry after empty)
 * - otherwise: return fresh cache immediately; if stale, return cache and
 *   optionally start a background refresh (caller decides whether to await)
 */
export async function loadOverviewWithSessionCache(
  fetchFresh: () => Promise<MetricResult[]>,
  options: { force?: boolean; now?: number } = {},
): Promise<{
  entry: OverviewCacheEntry;
  fromCache: boolean;
  /** Present when a silent revalidation was started (or shared in-flight). */
  background: Promise<OverviewCacheEntry> | null;
}> {
  const force = options.force === true;
  const now = options.now ?? Date.now();
  const cached = entry;

  if (!force && cached && isOverviewCacheFresh(cached, now)) {
    return { entry: cached, fromCache: true, background: null };
  }

  if (!force && cached) {
    return {
      entry: cached,
      fromCache: true,
      background: ensureOverviewFetch(fetchFresh),
    };
  }

  const next = await ensureOverviewFetch(fetchFresh);
  return { entry: next, fromCache: false, background: null };
}

function ensureOverviewFetch(
  fetchFresh: () => Promise<MetricResult[]>,
): Promise<OverviewCacheEntry> {
  if (inflight) return inflight;
  inflight = (async () => {
    try {
      const metrics = await fetchFresh();
      return setOverviewCache(metrics);
    } finally {
      inflight = null;
    }
  })();
  return inflight;
}

/** Test helper — replace clock-sensitive state between cases. */
export function __resetOverviewCacheForTests(): void {
  clearOverviewCache();
}
