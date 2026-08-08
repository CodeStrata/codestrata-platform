import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import type { ReactNode } from "react";
import { AppShell } from "../components/AppShell";
import { DashboardPage, PlaceholderSectionPage } from "../pages/DashboardPage";
import { LoginPage, SessionLoading } from "../pages/LoginPage";
import { AuthProvider, useAuth } from "../auth/AuthContext";
import {
  HttpInsightsApiClient,
  resolveInsightsApiBaseUrl,
} from "../api/authClient";
import type { InsightsApiClient } from "../api/insightsApi";
import type { InsightsAuthClient } from "../api/authClient";
import { DashboardErrorBoundary } from "../components/DashboardErrorBoundary";

function ProtectedApp({ client }: { client: InsightsApiClient }): ReactNode {
  const { state } = useAuth();
  if (state === "loading") {
    return <SessionLoading />;
  }
  if (state === "unauthenticated") {
    return <LoginPage />;
  }
  return (
    <AppShell>
      <DashboardErrorBoundary>
        <Routes>
          <Route path="/" element={<DashboardPage client={client} />} />
          <Route path="/dashboard" element={<Navigate to="/" replace />} />
          <Route path="/login" element={<Navigate to="/" replace />} />
          <Route
            path="/adoption"
            element={
              <PlaceholderSectionPage
                title="Adoption"
                note="CLI and VS Code version adoption."
                client={client}
                focusSection="adoption"
              />
            }
          />
          <Route
            path="/assessments"
            element={
              <PlaceholderSectionPage
                title="Assessments"
                note="First, repeat, successful, and failed assessment metrics."
                client={client}
                focusSection="assessments"
              />
            }
          />
          <Route
            path="/technology"
            element={
              <PlaceholderSectionPage
                title="Technology"
                note="Primary language and package ecosystem distributions."
                client={client}
                focusSection="technology"
              />
            }
          />
          <Route
            path="/ai"
            element={
              <PlaceholderSectionPage
                title="AI"
                note="Provider family and model family adoption."
                client={client}
                focusSection="ai"
              />
            }
          />
          <Route
            path="/releases"
            element={
              <PlaceholderSectionPage
                title="Releases"
                note="Separate CLI and VS Code release distributions."
                client={client}
                focusSection="adoption"
              />
            }
          />
          <Route
            path="/validation"
            element={
              <PlaceholderSectionPage
                title="Validation"
                note="External validation dataset size."
                client={client}
                focusSection="validation"
              />
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </DashboardErrorBoundary>
    </AppShell>
  );
}

export function App({
  apiClient,
  authClient,
}: {
  apiClient?: InsightsApiClient;
  authClient?: InsightsAuthClient;
} = {}): ReactNode {
  const client =
    apiClient ??
    new HttpInsightsApiClient({ apiBaseUrl: resolveInsightsApiBaseUrl() });

  return (
    <BrowserRouter>
      <AuthProvider authClient={authClient}>
        <ProtectedApp client={client} />
      </AuthProvider>
    </BrowserRouter>
  );
}
