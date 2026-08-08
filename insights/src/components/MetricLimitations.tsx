import type { ReactNode } from "react";
import { humanizeLimitations } from "../dashboard/labels";

export function MetricLimitations({ codes }: { codes: string[] }): ReactNode {
  const lines = humanizeLimitations(codes);
  if (lines.length === 0) return null;
  return (
    <ul className="cs-metric-limitations" aria-label="Metric limitations">
      {lines.map((line) => (
        <li key={line}>{line}</li>
      ))}
    </ul>
  );
}
