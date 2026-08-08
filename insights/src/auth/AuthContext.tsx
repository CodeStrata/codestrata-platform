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
  type InsightsAuthClient,
} from "../api/authClient";

export type SessionState = "loading" | "authenticated" | "unauthenticated";

interface AuthContextValue {
  state: SessionState;
  login: (password: string) => Promise<void>;
  logout: () => Promise<void>;
  loginError: string | null;
  clearLoginError: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

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
          setState(session.authenticated ? "authenticated" : "unauthenticated");
        }
      } catch {
        if (!cancelled) setState("unauthenticated");
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
        setState("authenticated");
      } catch {
        setState("unauthenticated");
        setLoginError("Invalid password");
        throw new Error("login_failed");
      }
    },
    [client],
  );

  const logout = useCallback(async () => {
    try {
      await client.logout();
    } finally {
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
