/** Published Reports page — index only; rendering stays on reports.codestrata.ai */

import { useEffect, useState, type ReactNode } from "react";
import { AuthApiError } from "../api/authClient";
import type { InsightsApiClient, PublishedReportsRegistry } from "../api/insightsApi";
import { useAuth } from "../auth/AuthContext";
import { ErrorState, LoadingState } from "../states/StateComponents";

function StatusPill({ status }: { status: string | null | undefined }): ReactNode {
  const value = (status || "unknown").toLowerCase();
  return <span className={`cs-badge cs-badge--status-${value}`}>{value}</span>;
}

function ReportLink({
  url,
  label,
}: {
  url: string | null | undefined;
  label: string;
}): ReactNode {
  if (!url) return <span className="cs-muted">—</span>;
  return (
    <a className="cs-text-link" href={url} target="_blank" rel="noopener noreferrer">
      {label}
    </a>
  );
}

function formatVerified(value: unknown): string {
  if (value == null) return "—";
  if (typeof value === "number" || typeof value === "string") return String(value);
  if (typeof value === "object") {
    const obj = value as Record<string, unknown>;
    if ("current_http" in obj) return `current=${String(obj.current_http)}`;
  }
  return "—";
}

export function PublishedReportsPage({
  client,
}: {
  client: InsightsApiClient;
}): ReactNode {
  const { logout } = useAuth();
  const [data, setData] = useState<PublishedReportsRegistry | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      setLoading(true);
      setError(null);
      try {
        const registry = await client.getPublishedReports();
        if (!cancelled) setData(registry);
      } catch (err) {
        if (err instanceof AuthApiError && err.code === "unauthenticated") {
          await logout();
          return;
        }
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unable to load published reports");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [client, logout]);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;
  if (!data) {
    return <ErrorState message="No published reports registry available." />;
  }

  const assessments = data.assessments ?? [];
  const eirs = data.engineering_intelligence ?? [];

  return (
    <div className="cs-page">
      <header className="cs-page-header">
        <p className="cs-eyebrow">Validation / release</p>
        <h1>Published Reports</h1>
        <p>
          Operator index of explicitly published Assessment and Engineering Intelligence
          reports. Links open the public reports domain. This is not a report editor.
        </p>
      </header>

      <section className="cs-section" aria-labelledby="assessments-heading">
        <h2 id="assessments-heading">Assessment Reports</h2>
        <p className="cs-section-note">One repository per row. Current and previous only.</p>
        {assessments.length === 0 ? (
          <div className="cs-state cs-state--zero" role="status">
            <strong>None yet</strong>
            <span>Publish a validation assessment to populate this list.</span>
          </div>
        ) : (
          <div className="cs-table-wrap">
            <table className="cs-table">
              <thead>
                <tr>
                  <th scope="col">Repository</th>
                  <th scope="col">Current</th>
                  <th scope="col">Previous</th>
                  <th scope="col">Status</th>
                  <th scope="col">Last verified</th>
                </tr>
              </thead>
              <tbody>
                {assessments.map((row) => (
                  <tr key={row.repository_id}>
                    <td>{row.repository_id}</td>
                    <td>
                      <ReportLink url={row.current_public_url} label="Open current" />
                    </td>
                    <td>
                      <ReportLink url={row.previous_public_url} label="Open previous" />
                    </td>
                    <td>
                      <StatusPill status={row.current_status} />
                    </td>
                    <td className="cs-muted">{formatVerified(row.last_verified_status)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="cs-section" aria-labelledby="eir-heading">
        <h2 id="eir-heading">Engineering Intelligence Reports</h2>
        <p className="cs-section-note">
          Portfolio / collection reports — not individual repository assessments.
        </p>
        {eirs.length === 0 ? (
          <div className="cs-state cs-state--zero" role="status">
            <strong>None yet</strong>
            <span>Publish a portfolio EIR to populate this list.</span>
          </div>
        ) : (
          <div className="cs-table-wrap">
            <table className="cs-table">
              <thead>
                <tr>
                  <th scope="col">Portfolio</th>
                  <th scope="col">Current</th>
                  <th scope="col">Previous</th>
                  <th scope="col">Status</th>
                  <th scope="col">Last verified</th>
                </tr>
              </thead>
              <tbody>
                {eirs.map((row) => (
                  <tr key={row.portfolio_id}>
                    <td>{row.portfolio_id}</td>
                    <td>
                      <ReportLink url={row.current_public_url} label="Open current" />
                    </td>
                    <td>
                      <ReportLink url={row.previous_public_url} label="Open previous" />
                    </td>
                    <td>
                      <StatusPill status={row.current_status} />
                    </td>
                    <td className="cs-muted">{formatVerified(row.last_verified_status)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
