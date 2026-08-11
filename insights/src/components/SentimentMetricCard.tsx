import type { ReactNode } from "react";
import type { MetricResult } from "../metrics/metricResult";
import {
  CompletenessBadge,
  LoadingState,
  UnavailableState,
} from "../states/StateComponents";
import { MetricLimitations } from "./MetricLimitations";
import { formatCount, formatShare } from "../dashboard/format";

/**
 * Community Sentiment — voluntary Yes/No feedback only.
 * Zero responses shows "No responses yet" (never "0% Positive").
 */
export function SentimentMetricCard({
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
  if (!result || result.status === "error") {
    return (
      <article className="cs-metric-card cs-metric-card--headline">
        <header className="cs-metric-card__header">
          <h3>{title}</h3>
          {result ? <CompletenessBadge completeness={result.completeness} /> : null}
        </header>
        <UnavailableState reason="Sentiment temporarily unavailable." />
        {result ? <MetricLimitations codes={result.limitations} /> : null}
      </article>
    );
  }

  const responseCount =
    typeof result.denominator === "number" ? result.denominator : null;
  const noResponsesYet =
    result.completeness === "complete" &&
    (responseCount === 0 ||
      result.limitations.includes("no_responses_yet") ||
      (result.value === null && responseCount === null));

  if (noResponsesYet) {
    return (
      <article className="cs-metric-card cs-metric-card--headline">
        <header className="cs-metric-card__header">
          <h3>{title}</h3>
          <CompletenessBadge completeness={result.completeness} />
        </header>
        <p className="cs-metric-card__value" data-testid={`value-${result.metric_id}`}>
          No responses yet
        </p>
        <p className="cs-muted">Voluntary Yes/No feedback</p>
        <MetricLimitations codes={result.limitations} />
      </article>
    );
  }

  if (result.completeness === "unavailable" || result.value === null) {
    return (
      <article className="cs-metric-card cs-metric-card--headline">
        <header className="cs-metric-card__header">
          <h3>{title}</h3>
          <CompletenessBadge completeness={result.completeness} />
        </header>
        <UnavailableState reason="Not yet collected — voluntary feedback only." />
        <MetricLimitations codes={result.limitations} />
      </article>
    );
  }

  const positiveShare =
    typeof result.share === "number"
      ? result.share
      : typeof result.value === "number"
        ? result.value > 1
          ? result.value / 100
          : result.value
        : null;

  return (
    <article className="cs-metric-card cs-metric-card--headline">
      <header className="cs-metric-card__header">
        <h3>{title}</h3>
        <CompletenessBadge completeness={result.completeness} />
      </header>
      <p className="cs-metric-card__value" data-testid={`value-${result.metric_id}`}>
        {positiveShare !== null ? `${formatShare(positiveShare)} Positive` : "—"}
      </p>
      {responseCount !== null ? (
        <p className="cs-muted">{formatCount(responseCount)} responses</p>
      ) : null}
      <p className="cs-muted">Based on voluntary Yes/No feedback.</p>
      <MetricLimitations codes={result.limitations} />
    </article>
  );
}
