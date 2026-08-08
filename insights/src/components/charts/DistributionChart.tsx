import type { ReactNode } from "react";
import type { MetricGroup } from "../../metrics/metricResult";
import { formatCount, formatShare, groupLabel } from "../../dashboard/format";

export function MetricTable({
  caption,
  groups,
}: {
  caption: string;
  groups: MetricGroup[];
}): ReactNode {
  if (groups.length === 0) {
    return null;
  }
  return (
    <div className="cs-metric-table-wrap">
      <table className="cs-metric-table">
        <caption className="cs-sr-only">{caption}</caption>
        <thead>
          <tr>
            <th scope="col">Category</th>
            <th scope="col">Count</th>
            <th scope="col">Share</th>
          </tr>
        </thead>
        <tbody>
          {groups.map((g) => {
            const label = groupLabel(g.key, g.suppressed);
            const share = formatShare(g.share);
            return (
              <tr key={`${g.dimension}:${g.key}`}>
                <td>{label}</td>
                <td>{formatCount(g.count)}</td>
                <td>{share ?? "—"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/** Horizontal bar chart using Design System chart tokens — presentation only. */
export function HorizontalBarChart({
  title,
  description,
  groups,
}: {
  title: string;
  description: string;
  groups: MetricGroup[];
}): ReactNode {
  if (groups.length === 0) {
    return (
      <p className="cs-muted" role="status">
        No distribution groups for this metric.
      </p>
    );
  }
  const max = Math.max(...groups.map((g) => g.count), 1);
  const descId = `${title.replace(/\s+/g, "-").toLowerCase()}-desc`;

  return (
    <figure className="cs-bar-chart" aria-labelledby={`${descId}-title`} aria-describedby={descId}>
      <figcaption id={`${descId}-title`} className="cs-bar-chart__title">
        {title}
      </figcaption>
      <p id={descId} className="cs-sr-only">
        {description}
      </p>
      <ul className="cs-bar-chart__list" role="list">
        {groups.map((g, index) => {
          const label = groupLabel(g.key, g.suppressed);
          const share = formatShare(g.share);
          const pct = Math.max(2, Math.round((g.count / max) * 100));
          const colorVar = `var(--cs-chart-${(index % 5) + 1})`;
          return (
            <li key={`${g.dimension}:${g.key}`} className="cs-bar-chart__row">
              <div className="cs-bar-chart__label">
                <span>{label}</span>
                <span className="cs-bar-chart__meta">
                  {formatCount(g.count)}
                  {share ? ` · ${share}` : ""}
                </span>
              </div>
              <div
                className="cs-bar-chart__track"
                role="img"
                aria-label={`${label}: ${formatCount(g.count)}${share ? `, ${share}` : ""}`}
              >
                <div
                  className="cs-bar-chart__fill"
                  style={{ width: `${pct}%`, background: colorVar }}
                />
              </div>
            </li>
          );
        })}
      </ul>
      <MetricTable caption={`${title} data table`} groups={groups} />
    </figure>
  );
}
