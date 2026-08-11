import { useCallback, useEffect, useState, type ReactNode } from "react";
import type { InsightsApiClient } from "../api/insightsApi";
import { AuthApiError } from "../api/authClient";
import type { MetricResult } from "../metrics/metricResult";
import { HeadlineMetricCard, Section } from "../components/MetricCard";
import { SentimentMetricCard } from "../components/SentimentMetricCard";
import { METRIC_DISPLAY_NAMES, V02_OVERVIEW_METRIC_IDS } from "../dashboard/labels";
import { useAuth } from "../auth/AuthContext";
import {
  clearOverviewCache,
  isOverviewCacheFresh,
  loadOverviewWithSessionCache,
  peekOverviewCache,
} from "../api/sessionOverviewCache";

function byId(results: MetricResult[], id: string): MetricResult | undefined {
  return results.find((r) => r.metric_id === id);
}

function formatRefreshedAt(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "medium",
    });
  } catch {
    return iso;
  }
}

function applyEntry(
  entry: { metrics: MetricResult[]; fetchedAt: number },
  setResults: (m: MetricResult[]) => void,
  setLastRefreshedAt: (iso: string) => void,
): void {
  setResults(entry.metrics);
  setLastRefreshedAt(new Date(entry.fetchedAt).toISOString());
}

export function DashboardPage({
  client,
}: {
  client: InsightsApiClient;
  focusSection?: string;
}): ReactNode {
  const { logout } = useAuth();
  const [loading, setLoading] = useState(() => peekOverviewCache() == null);
  const [refreshing, setRefreshing] = useState(false);
  const [results, setResults] = useState<MetricResult[]>(
    () => peekOverviewCache()?.metrics ?? [],
  );
  const [loadError, setLoadError] = useState<string | null>(null);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<string | null>(() => {
    const cached = peekOverviewCache();
    return cached ? new Date(cached.fetchedAt).toISOString() : null;
  });
  const [staleNotice, setStaleNotice] = useState(false);

  const handleAuthFailure = useCallback(async () => {
    clearOverviewCache();
    setResults([]);
    setLastRefreshedAt(null);
    setStaleNotice(false);
    await logout();
  }, [logout]);

  const applyBackground = useCallback(
    async (background: Promise<{ metrics: MetricResult[]; fetchedAt: number }>) => {
      try {
        const next = await background;
        applyEntry(next, setResults, setLastRefreshedAt);
        setLoadError(null);
        setStaleNotice(false);
      } catch (err) {
        if (err instanceof AuthApiError && err.code === "unauthenticated") {
          await handleAuthFailure();
          return;
        }
        // Keep cached metrics; Last refreshed stays truthful for the last success.
        setStaleNotice(true);
        if (err instanceof AuthApiError && err.code === "access_denied") {
          setLoadError("Access denied. Showing last successful dashboard data.");
        } else {
          setLoadError(
            "Could not refresh metrics. Showing last successful dashboard data.",
          );
        }
      }
    },
    [handleAuthFailure],
  );

  const load = useCallback(
    async (mode: "initial" | "refresh") => {
      const force = mode === "refresh";
      const cached = peekOverviewCache();

      if (mode === "initial" && cached) {
        applyEntry(cached, setResults, setLastRefreshedAt);
        setLoading(false);
        if (isOverviewCacheFresh(cached)) {
          setLoadError(null);
          setStaleNotice(false);
          return;
        }
        // Stale cache: keep UI populated and revalidate silently (no Refresh spinner).
        setLoadError(null);
        const { background } = await loadOverviewWithSessionCache(
          () => client.getOverview(),
          { force: false },
        );
        if (background) void applyBackground(background);
        return;
      }

      if (mode === "initial") setLoading(true);
      else setRefreshing(true);
      setLoadError(null);
      setStaleNotice(false);
      try {
        const { entry, background } = await loadOverviewWithSessionCache(
          () => client.getOverview(),
          { force },
        );
        applyEntry(entry, setResults, setLastRefreshedAt);
        if (background) void applyBackground(background);
      } catch (err) {
        if (err instanceof AuthApiError && err.code === "unauthenticated") {
          await handleAuthFailure();
          return;
        }
        const stillHaveCache = peekOverviewCache();
        if (stillHaveCache) {
          applyEntry(stillHaveCache, setResults, setLastRefreshedAt);
          setStaleNotice(true);
          if (err instanceof AuthApiError && err.code === "access_denied") {
            setLoadError("Access denied. Showing last successful dashboard data.");
          } else {
            setLoadError(
              "Could not refresh metrics. Showing last successful dashboard data.",
            );
          }
        } else if (err instanceof AuthApiError && err.code === "access_denied") {
          setLoadError("Access denied.");
          if (mode === "initial") setResults([]);
        } else {
          setLoadError("Insights metrics are temporarily unavailable.");
          if (mode === "initial") setResults([]);
        }
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [applyBackground, client, handleAuthFailure],
  );

  useEffect(() => {
    void load("initial");
  }, [load]);

  return (
    <div className="cs-page">
      <header className="cs-page-header">
        <p className="cs-header__eyebrow">Internal only</p>
        <h1>CodeStrata Community Insights</h1>
        <p>
          v0.2.0 Community adoption metrics from the Platform aggregation
          service. This UI does not invent or recompute metric values.
        </p>
        <div className="cs-page-header__actions">
          <button
            type="button"
            className="cs-button"
            disabled={loading || refreshing}
            onClick={() => void load("refresh")}
            data-testid="refresh-dashboard"
          >
            {refreshing ? "Refreshing…" : "Refresh Dashboard"}
          </button>
          {lastRefreshedAt ? (
            <span className="cs-muted" data-testid="last-refreshed">
              Last refreshed: {formatRefreshedAt(lastRefreshedAt)}
              {staleNotice ? " (cached)" : ""}
            </span>
          ) : null}
        </div>
        {loadError ? (
          <div className="cs-state cs-state--error" role="alert">
            <strong>
              {results.length > 0 ? "Refresh unavailable" : "Dashboard unavailable"}
            </strong>
            <span>{loadError}</span>
            <button type="button" className="cs-button" onClick={() => void load("refresh")}>
              Retry
            </button>
          </div>
        ) : null}
      </header>

      <Section id="community-pulse" title="Community pulse">
        <HeadlineMetricCard
          title={METRIC_DISPLAY_NAMES.github_stars}
          loading={loading}
          result={byId(results, "github_stars")}
        />
        <HeadlineMetricCard
          title={METRIC_DISPLAY_NAMES.github_forks}
          loading={loading}
          result={byId(results, "github_forks")}
        />
        <SentimentMetricCard
          title={METRIC_DISPLAY_NAMES.community_sentiment}
          loading={loading}
          result={byId(results, "community_sentiment")}
        />
      </Section>

      <Section id="assessments" title="Assessments">
        <HeadlineMetricCard
          title={METRIC_DISPLAY_NAMES.total_assessments}
          loading={loading}
          result={byId(results, "total_assessments")}
        />
        <HeadlineMetricCard
          title={METRIC_DISPLAY_NAMES.first_assessments}
          loading={loading}
          result={byId(results, "first_assessments")}
        />
        <HeadlineMetricCard
          title={METRIC_DISPLAY_NAMES.repeat_assessments}
          loading={loading}
          result={byId(results, "repeat_assessments")}
        />
      </Section>

      <Section id="reliability" title="Reliability & publishing">
        <HeadlineMetricCard
          title={METRIC_DISPLAY_NAMES.successful_assessments}
          loading={loading}
          result={byId(results, "successful_assessments")}
        />
        <HeadlineMetricCard
          title={METRIC_DISPLAY_NAMES.failed_assessments}
          loading={loading}
          result={byId(results, "failed_assessments")}
        />
        <HeadlineMetricCard
          title={METRIC_DISPLAY_NAMES.published_reports}
          loading={loading}
          result={byId(results, "published_reports")}
        />
      </Section>

      <p className="cs-muted cs-sr-only">
        Overview metric order: {V02_OVERVIEW_METRIC_IDS.join(", ")}
      </p>
    </div>
  );
}

export function PlaceholderSectionPage({
  note,
  client,
}: {
  title: string;
  note: string;
  client: InsightsApiClient;
  focusSection: string;
}): ReactNode {
  return (
    <>
      <p className="cs-sr-only">{note}</p>
      <DashboardPage client={client} />
    </>
  );
}
