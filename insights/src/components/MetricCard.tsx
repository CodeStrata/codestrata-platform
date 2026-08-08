import type { ReactNode } from "react";
import type { MetricResult } from "../metrics/metricResult";
import { SUPPRESSED_GROUP_KEY } from "../metrics/metricResult";
import {
  CompletenessBadge,
  EmptyZeroState,
  LoadingState,
  NotApplicableState,
  PartialState,
  StatusBadge,
  UnavailableState,
} from "../states/StateComponents";
import { formatCount } from "../dashboard/format";
import { HorizontalBarChart } from "./charts/DistributionChart";
import { MetricLimitations } from "./MetricLimitations";

export function HeadlineMetricCard({
  title,
  result,
  loading = false,
}: {
  title: string;
  result?: MetricResult | null;
  loading?: boolean;
}): ReactNode {
  if (loading) {
    return (
      <article className="cs-metric-card cs-metric-card--headline" aria-busy="true">
        <h3>{title}</h3>
        <LoadingState />
      </article>
    );
  }
  if (!result) {
    return (
      <article className="cs-metric-card cs-metric-card--headline">
        <h3>{title}</h3>
        <UnavailableState reason="Metric is not currently available." />
      </article>
    );
  }
  if (result.status === "error" || result.completeness === "unavailable") {
    return (
      <article className="cs-metric-card cs-metric-card--headline">
        <header className="cs-metric-card__header">
          <h3>{title}</h3>
          <CompletenessBadge completeness={result.completeness} />
        </header>
        <UnavailableState reason="Metric is not currently available." />
        <MetricLimitations codes={result.limitations} />
      </article>
    );
  }
  if (result.completeness === "not_applicable") {
    return (
      <article className="cs-metric-card cs-metric-card--headline">
        <h3>{title}</h3>
        <NotApplicableState />
      </article>
    );
  }

  const showZero = result.value === 0 && result.completeness === "complete";
  const windowLabel = `${result.window.start_date_utc} → ${result.window.end_date_utc} (${result.window.horizon})`;

  return (
    <article className="cs-metric-card cs-metric-card--headline">
      <header className="cs-metric-card__header">
        <h3>{title}</h3>
        <div className="cs-metric-card__badges">
          <StatusBadge status={result.status} />
          <CompletenessBadge completeness={result.completeness} />
        </div>
      </header>
      {showZero ? (
        <EmptyZeroState label={title} />
      ) : (
        <p className="cs-metric-card__value" data-testid={`value-${result.metric_id}`}>
          {formatCount(result.value)}
        </p>
      )}
      <p className="cs-metric-card__window cs-muted">{windowLabel}</p>
      {result.completeness === "partial" ? (
        <PartialState note="Partial data — some eligible events could not be included." />
      ) : null}
      <MetricLimitations codes={result.limitations} />
    </article>
  );
}

export function MetricCard(props: {
  title: string;
  result?: MetricResult | null;
  loading?: boolean;
}): ReactNode {
  return <HeadlineMetricCard {...props} />;
}

export function DistributionMetric({
  title,
  description,
  result,
  loading = false,
  dimensionFilter,
}: {
  title: string;
  description: string;
  result?: MetricResult | null;
  loading?: boolean;
  dimensionFilter?: string;
}): ReactNode {
  if (loading) {
    return (
      <section className="cs-chart-container" aria-busy="true">
        <h3>{title}</h3>
        <LoadingState />
      </section>
    );
  }
  if (!result || result.completeness === "unavailable" || result.status === "error") {
    return (
      <section className="cs-chart-container">
        <h3>{title}</h3>
        <UnavailableState reason="Metric is not currently available." />
        {result ? <MetricLimitations codes={result.limitations} /> : null}
      </section>
    );
  }
  if (result.completeness === "not_applicable") {
    return (
      <section className="cs-chart-container">
        <h3>{title}</h3>
        <NotApplicableState />
      </section>
    );
  }

  const groups = dimensionFilter
    ? result.groups.filter((g) => g.dimension === dimensionFilter)
    : result.groups;

  const safeGroups = groups.map((g) => ({
    ...g,
    key: g.suppressed || g.key === SUPPRESSED_GROUP_KEY ? "other_suppressed" : g.key,
  }));

  return (
    <section className="cs-chart-container">
      <header className="cs-metric-card__header">
        <h3>{title}</h3>
        <div className="cs-metric-card__badges">
          <StatusBadge status={result.status} />
          <CompletenessBadge completeness={result.completeness} />
        </div>
      </header>
      {result.value !== null ? (
        <p className="cs-muted">
          Total: {formatCount(result.value)}
          {result.denominator !== null
            ? ` · Denominator: ${formatCount(result.denominator)}`
            : ""}
        </p>
      ) : null}
      {result.completeness === "partial" ? <PartialState /> : null}
      <HorizontalBarChart title={title} description={description} groups={safeGroups} />
      <MetricLimitations codes={result.limitations} />
    </section>
  );
}

export function ChartContainer({
  title,
  children,
}: {
  title: string;
  children?: ReactNode;
}): ReactNode {
  return (
    <section className="cs-chart-container" aria-label={title}>
      <h3>{title}</h3>
      <div className="cs-chart-container__body">{children}</div>
    </section>
  );
}

export function Section({
  id,
  title,
  children,
}: {
  id: string;
  title: string;
  children: ReactNode;
}): ReactNode {
  return (
    <section id={id} className="cs-section" aria-labelledby={`${id}-heading`}>
      <h2 id={`${id}-heading`}>{title}</h2>
      <div className="cs-section__grid">{children}</div>
    </section>
  );
}
