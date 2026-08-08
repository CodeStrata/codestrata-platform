import { useCallback, useEffect, useState, type ReactNode } from "react";
import type { InsightsApiClient } from "../api/insightsApi";
import { AuthApiError } from "../api/authClient";
import type { MetricResult } from "../metrics/metricResult";
import {
  DistributionMetric,
  HeadlineMetricCard,
  Section,
} from "../components/MetricCard";
import { METRIC_DISPLAY_NAMES } from "../dashboard/labels";
import { useAuth } from "../auth/AuthContext";

function byId(results: MetricResult[], id: string): MetricResult | undefined {
  return results.find((r) => r.metric_id === id);
}

export function DashboardPage({
  client,
  focusSection,
}: {
  client: InsightsApiClient;
  focusSection?: string;
}): ReactNode {
  const { logout } = useAuth();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [results, setResults] = useState<MetricResult[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [fetchedLabel, setFetchedLabel] = useState<string | null>(null);

  const load = useCallback(
    async (mode: "initial" | "refresh") => {
      if (mode === "initial") setLoading(true);
      else setRefreshing(true);
      setLoadError(null);
      try {
        const overview = await client.getOverview();
        setResults(overview);
        setFetchedLabel("Fetched on last refresh");
      } catch (err) {
        if (err instanceof AuthApiError && err.code === "unauthenticated") {
          await logout();
          return;
        }
        if (err instanceof AuthApiError && err.code === "access_denied") {
          setLoadError("Access denied.");
        } else {
          setLoadError("Insights metrics are temporarily unavailable.");
        }
        // Keep prior results on refresh failure.
        if (mode === "initial") setResults([]);
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [client, logout],
  );

  useEffect(() => {
    void load("initial");
  }, [load]);

  useEffect(() => {
    if (!focusSection) return;
    const el = document.getElementById(focusSection);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [focusSection, results, loading]);

  return (
    <div className="cs-page">
      <header className="cs-page-header">
        <p className="cs-header__eyebrow">Internal only</p>
        <h1>CodeStrata Community Insights</h1>
        <p>
          Aggregate Community Edition adoption metrics. Values come from the Platform
          aggregation service — this UI does not compute metric semantics.
        </p>
        <p className="cs-muted">
          Updated on dashboard refresh, subject to ingestion availability.
        </p>
        <div className="cs-page-header__actions">
          <button
            type="button"
            className="cs-button"
            disabled={loading || refreshing}
            onClick={() => void load("refresh")}
          >
            {refreshing ? "Refreshing…" : "Refresh dashboard"}
          </button>
          {fetchedLabel ? <span className="cs-muted">{fetchedLabel}</span> : null}
        </div>
        {loadError ? (
          <div className="cs-state cs-state--error" role="alert">
            <strong>Dashboard unavailable</strong>
            <span>{loadError}</span>
            <button type="button" className="cs-button" onClick={() => void load("initial")}>
              Retry
            </button>
          </div>
        ) : null}
      </header>

      <Section id="activity" title="Community Activity">
        <HeadlineMetricCard
          title={METRIC_DISPLAY_NAMES.total_anonymous_installations}
          loading={loading}
          result={byId(results, "total_anonymous_installations")}
        />
        <HeadlineMetricCard
          title={METRIC_DISPLAY_NAMES.daily_active_installations}
          loading={loading}
          result={byId(results, "daily_active_installations")}
        />
        <HeadlineMetricCard
          title={METRIC_DISPLAY_NAMES.monthly_active_installations}
          loading={loading}
          result={byId(results, "monthly_active_installations")}
        />
      </Section>

      <Section id="assessments" title="Assessments">
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
      </Section>

      <Section id="adoption" title="Adoption">
        <DistributionMetric
          title={METRIC_DISPLAY_NAMES.cli_version_adoption}
          description="CLI version distribution from server-returned groups and shares."
          loading={loading}
          result={byId(results, "cli_version_adoption")}
        />
        <DistributionMetric
          title={METRIC_DISPLAY_NAMES.vscode_extension_usage}
          description="VS Code extension usage distribution from server-returned groups."
          loading={loading}
          result={byId(results, "vscode_extension_usage")}
        />
        <DistributionMetric
          title="CLI release adoption"
          description="CLI release versions only — not merged with VS Code."
          loading={loading}
          result={byId(results, "release_adoption")}
          dimensionFilter="cli_client_version"
        />
        <DistributionMetric
          title="VS Code extension release adoption"
          description="VS Code extension release versions only — not merged with CLI."
          loading={loading}
          result={byId(results, "release_adoption")}
          dimensionFilter="vscode_client_version"
        />
      </Section>

      <Section id="coverage" title="Assessment Coverage">
        <DistributionMetric
          title={METRIC_DISPLAY_NAMES.assessment_head_usage}
          description="Assessment heads present in completed or partial assessments."
          loading={loading}
          result={byId(results, "assessment_head_usage")}
        />
      </Section>

      <Section id="technology" title="Technology">
        <DistributionMetric
          title="Primary language distribution"
          description="Normalized primary-language categories. Not package ecosystems."
          loading={loading}
          result={byId(results, "language_ecosystem_distribution")}
          dimensionFilter="primary_language"
        />
        <DistributionMetric
          title="Package ecosystem distribution"
          description="Normalized package ecosystems. Separate from primary language."
          loading={loading}
          result={byId(results, "language_ecosystem_distribution")}
          dimensionFilter="package_ecosystem"
        />
      </Section>

      <Section id="ai" title="AI Adoption">
        <DistributionMetric
          title={METRIC_DISPLAY_NAMES.ai_provider_adoption}
          description="Provider-family adoption shares from the aggregation service."
          loading={loading}
          result={byId(results, "ai_provider_adoption")}
        />
        <DistributionMetric
          title={METRIC_DISPLAY_NAMES.ai_model_adoption}
          description="AI model family adoption only — exact model IDs are never shown."
          loading={loading}
          result={byId(results, "ai_model_adoption")}
        />
      </Section>

      <Section id="validation" title="Validation Dataset">
        <HeadlineMetricCard
          title={METRIC_DISPLAY_NAMES.validation_dataset_growth}
          loading={loading}
          result={byId(results, "validation_dataset_growth")}
        />
        <p className="cs-muted">
          Historical growth tracking is not available yet. Current catalog size only.
        </p>
      </Section>
    </div>
  );
}

export function PlaceholderSectionPage({
  note,
  client,
  focusSection,
}: {
  title: string;
  note: string;
  client: InsightsApiClient;
  focusSection: string;
}): ReactNode {
  return (
    <>
      <p className="cs-sr-only">{note}</p>
      <DashboardPage client={client} focusSection={focusSection} />
    </>
  );
}
