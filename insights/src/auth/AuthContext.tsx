import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  HttpInsightsAuthClient,
  resolveInsightsApiBaseUrl,
  AuthApiError,
  type InsightsAuthClient,
} from "../api/authClient";
import { clearOverviewCache } from "../api/sessionOverviewCache";

export type SessionState = "loading" | "authenticated" | "unauthenticated";

interface AuthContextValue {
  state: SessionState;
  login: (password: string) => Promise<void>;
  logout: () => Promise<void>;
  loginError: string | null;
  clearLoginError: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function endAuthenticatedSession(): void {
  // Never retain prior-session dashboard metrics across auth boundaries.
  clearOverviewCache();
}

export function AuthProvider({
  children,
  authClient,
}: {
  children: ReactNode;
  authClient?: InsightsAuthClient;
}): ReactNode {
  const client = useMemo(
    () =>
      authClient ??
      new HttpInsightsAuthClient({ apiBaseUrl: resolveInsightsApiBaseUrl() }),
    [authClient],
  );
  const [state, setState] = useState<SessionState>("loading");
  const [loginError, setLoginError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const session = await client.getSession();
        if (!cancelled) {
          if (session.authenticated) {
            setState("authenticated");
          } else {
            endAuthenticatedSession();
            setState("unauthenticated");
          }
        }
      } catch {
        if (!cancelled) {
          endAuthenticatedSession();
          setState("unauthenticated");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [client]);

  const login = useCallback(
    async (password: string) => {
      setLoginError(null);
      try {
        await client.login(password);
        // New session — do not reuse any pre-login cache (should already be empty).
        clearOverviewCache();
        setState("authenticated");
      } catch (err) {
        endAuthenticatedSession();
        setState("unauthenticated");
        if (err instanceof AuthApiError && err.code === "unavailable") {
          setLoginError("Authentication unavailable. Try again shortly.");
        } else if (err instanceof AuthApiError && err.code === "access_denied") {
          setLoginError("Request blocked. Refresh and try again.");
        } else if (err instanceof AuthApiError && err.code === "rate_limited") {
          setLoginError("Too many attempts. Wait briefly and try again.");
        } else if (err instanceof AuthApiError && err.code === "invalid_credentials") {
          setLoginError("Invalid password");
        } else if (err instanceof AuthApiError && err.code === "invalid_request") {
          setLoginError("Enter the dashboard password.");
        } else if (err instanceof AuthApiError && err.code === "network_error") {
          setLoginError("Network error. Check connection and try again.");
        } else {
          setLoginError("Sign-in failed. Try again.");
        }
        throw new Error("login_failed");
      }
    },
    [client],
  );

  const logout = useCallback(async () => {
    try {
      await client.logout();
    } finally {
      endAuthenticatedSession();
      setState("unauthenticated");
      setLoginError(null);
    }
  }, [client]);

  const clearLoginError = useCallback(() => setLoginError(null), []);

  const value = useMemo(
    () => ({ state, login, logout, loginError, clearLoginError }),
    [state, login, logout, loginError, clearLoginError],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth requires AuthProvider");
  }
  return ctx;
}
