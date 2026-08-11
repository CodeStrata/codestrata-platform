/** Validation Reports — temporary internal Community validation corpus index.

Rendering stays on reports.codestrata.ai opaque URLs. Not a permanent product
surface; removable when commercial portfolio/report management replaces it.
*/

import { useCallback, useEffect, useState, type ReactNode } from "react";
import { AuthApiError } from "../api/authClient";
import type {
  InsightsApiClient,
  ValidationReportRow,
  ValidationReportsPage as ValidationPage,
} from "../api/insightsApi";
import { useAuth } from "../auth/AuthContext";
import { ErrorState, LoadingState } from "../states/StateComponents";

const PAGE_LIMIT = 50;

function StatusPill({ status }: { status: string | null | undefined }): ReactNode {
  const value = (status || "unknown").toLowerCase().replace(/_/g, "-");
  return <span className={`cs-badge cs-badge--status-${value}`}>{status || "unknown"}</span>;
}

function formatWhen(value: string | null | undefined): string {
  if (!value) return "—";
  const d = Date.parse(value);
  if (Number.isNaN(d)) return value;
  return new Date(d).toISOString().replace("T", " ").replace(/\.\d+Z$/, " UTC");
}

function assessmentLabel(row: ValidationReportRow): string {
  const t = (row.report_type || "").trim();
  if (t === "engineering_intelligence") return "Engineering Intelligence";
  if (t === "assessment") return "Assessment";
  return t || "—";
}

export function PublishedReportsPage({
  client,
}: {
  client: InsightsApiClient;
}): ReactNode {
  const { logout } = useAuth();
  const [page, setPage] = useState<ValidationPage | null>(null);
  const [cursorStack, setCursorStack] = useState<(string | null)[]>([null]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(
    async (cursor: string | null) => {
      setLoading(true);
      setError(null);
      try {
        const next = await client.getValidationReports({
          limit: PAGE_LIMIT,
          cursor: cursor ?? undefined,
        });
        setPage(next);
      } catch (err) {
        if (err instanceof AuthApiError && err.code === "unauthenticated") {
          await logout();
          return;
        }
        setError(err instanceof Error ? err.message : "Unable to load validation reports");
      } finally {
        setLoading(false);
      }
    },
    [client, logout],
  );

  useEffect(() => {
    void load(null);
  }, [load]);

  const onNext = () => {
    if (!page?.next_cursor) return;
    setCursorStack((stack) => [...stack, page.next_cursor]);
    void load(page.next_cursor);
  };

  const onPrev = () => {
    if (cursorStack.length <= 1) return;
    const nextStack = cursorStack.slice(0, -1);
    setCursorStack(nextStack);
    void load(nextStack[nextStack.length - 1] ?? null);
  };

  if (loading && !page) return <LoadingState />;
  if (error && !page) return <ErrorState message={error} />;
  if (!page) {
    return <ErrorState message="No validation registry available." />;
  }

  const items = page.items ?? [];
  const pageIndex = cursorStack.length;

  return (
    <div className="cs-page">
      <header className="cs-page-header">
        <p className="cs-eyebrow">Temporary internal tooling</p>
        <h1>Validation Reports</h1>
        <p>
          Private Community validation corpus of successfully published and
          independently GET-verified reports. Opaque links only — this index is
          not public and does not make reports.codestrata.ai enumerable. Designed
          to be removed or replaced by commercial portfolio/report management
          without changing public report URL contracts.
        </p>
      </header>

      <section className="cs-section" aria-labelledby="validation-heading">
        <h2 id="validation-heading">Published validation corpus</h2>
        <p className="cs-section-note">
          Newest first. Page size {page.limit ?? PAGE_LIMIT}. Local release
          manifests remain export/snapshots of this registry.
        </p>
        {error ? <p className="cs-muted" role="status">{error}</p> : null}
        {items.length === 0 ? (
          <div className="cs-state cs-state--zero" role="status">
            <strong>None yet</strong>
            <span>Publish and verify a Community report to populate this list.</span>
          </div>
        ) : (
          <div className="cs-table-wrap">
            <table className="cs-table">
              <thead>
                <tr>
                  <th scope="col">Repository / Validation ID</th>
                  <th scope="col">Assessment Type</th>
                  <th scope="col">Published At</th>
                  <th scope="col">Verification Status</th>
                  <th scope="col">Open Report</th>
                </tr>
              </thead>
              <tbody>
                {items.map((row) => {
                  const identity =
                    row.display_identity ||
                    row.logical_identity_key ||
                    row.public_report_id ||
                    "—";
                  const openUrl =
                    row.public_url ||
                    (row.public_report_id
                      ? `https://reports.codestrata.ai/r/${row.public_report_id}`
                      : null);
                  return (
                    <tr key={row.public_report_id || identity}>
                      <td>{identity}</td>
                      <td>{assessmentLabel(row)}</td>
                      <td className="cs-muted">{formatWhen(row.published_at)}</td>
                      <td>
                        <StatusPill status={row.verification_status} />
                      </td>
                      <td>
                        {openUrl ? (
                          <a
                            className="cs-text-link"
                            href={openUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            Open Report
                          </a>
                        ) : (
                          <span className="cs-muted">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        <div className="cs-page-header__actions" style={{ marginTop: "1rem" }}>
          <button
            type="button"
            className="cs-button cs-button--ghost"
            disabled={pageIndex <= 1 || loading}
            onClick={onPrev}
          >
            Previous
          </button>
          <span className="cs-muted">Page {pageIndex}</span>
          <button
            type="button"
            className="cs-button cs-button--ghost"
            disabled={!page.next_cursor || loading}
            onClick={onNext}
          >
            Next
          </button>
        </div>
      </section>
    </div>
  );
}
