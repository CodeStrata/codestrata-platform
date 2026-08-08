import { useId, useState, type FormEvent, type ReactNode } from "react";
import { useAuth } from "../auth/AuthContext";

export function LoginPage(): ReactNode {
  const { login, loginError, clearLoginError } = useAuth();
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const errorId = useId();
  const passwordId = useId();

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    clearLoginError();
    setSubmitting(true);
    try {
      await login(password);
      setPassword("");
    } catch {
      // Error surfaced via loginError — generic message only.
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="cs-login">
      <div className="cs-login__panel">
        <img
          className="cs-login__logo"
          src="/brand/codestrata-lockup-horizontal-on-light.svg"
          alt="CodeStrata"
          width={200}
          height={40}
        />
        <h1>Community Insights</h1>
        <p className="cs-login__lead">
          Internal adoption analytics. Sign in with the shared dashboard password.
        </p>
        <form className="cs-login__form" onSubmit={onSubmit} noValidate>
          <div className="cs-field">
            <label htmlFor={passwordId}>Password</label>
            <input
              id={passwordId}
              name="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={submitting}
              required
              aria-invalid={loginError ? true : undefined}
              aria-describedby={loginError ? errorId : undefined}
            />
          </div>
          {loginError ? (
            <p id={errorId} className="cs-login__error" role="alert">
              {loginError}
            </p>
          ) : null}
          <button type="submit" className="cs-button" disabled={submitting || !password}>
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

export function SessionLoading(): ReactNode {
  return (
    <div className="cs-login" role="status" aria-live="polite">
      <p className="cs-login__loading">Checking session…</p>
    </div>
  );
}
