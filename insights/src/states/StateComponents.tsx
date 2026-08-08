import type { ReactNode } from "react";

export function CompletenessBadge({
  completeness,
}: {
  completeness: string;
}): ReactNode {
  const label =
    completeness === "unavailable"
      ? "Unavailable"
      : completeness === "partial"
        ? "Partial"
        : completeness === "not_applicable"
          ? "Not applicable"
          : completeness === "complete"
            ? "Complete"
            : completeness;
  return (
    <span className={`cs-badge cs-badge--${completeness}`} data-completeness={completeness}>
      {label}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }): ReactNode {
  return (
    <span className={`cs-badge cs-badge--status-${status}`} data-status={status}>
      {status}
    </span>
  );
}

export function LoadingState(): ReactNode {
  return (
    <div className="cs-state cs-state--loading" role="status" aria-live="polite">
      Loading metrics…
    </div>
  );
}

export function EmptyZeroState({ label }: { label: string }): ReactNode {
  return (
    <div className="cs-state cs-state--zero" role="status">
      <strong>0</strong>
      <span>{label}</span>
      <span className="cs-state__hint">Valid zero — not unavailable</span>
    </div>
  );
}

export function UnavailableState({ reason }: { reason?: string }): ReactNode {
  return (
    <div className="cs-state cs-state--unavailable" role="status">
      <strong>Unavailable</strong>
      <span>{reason ?? "Metric is not currently available."}</span>
      <span className="cs-state__hint">This is not a zero count</span>
    </div>
  );
}

export function NotApplicableState(): ReactNode {
  return (
    <div className="cs-state cs-state--na" role="status">
      <strong>Not applicable</strong>
      <span>This metric does not apply for the current window.</span>
    </div>
  );
}

export function PartialState({ note }: { note?: string }): ReactNode {
  return (
    <div className="cs-state cs-state--partial" role="status">
      <strong>Partial</strong>
      <span>{note ?? "Partial data — some eligible events could not be included."}</span>
    </div>
  );
}

export function ErrorState({ message }: { message?: string }): ReactNode {
  return (
    <div className="cs-state cs-state--error" role="alert">
      <strong>Error</strong>
      <span>{message ?? "Unable to load this metric."}</span>
    </div>
  );
}
