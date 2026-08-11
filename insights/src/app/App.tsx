import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import type { ReactNode } from "react";
import { AppShell } from "../components/AppShell";
import { DashboardPage } from "../pages/DashboardPage";
import { PublishedReportsPage } from "../pages/PublishedReportsPage";
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
            path="/published-reports"
            element={<PublishedReportsPage client={client} />}
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
