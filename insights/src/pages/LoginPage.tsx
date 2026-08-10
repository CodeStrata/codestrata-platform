import { useId, useRef, useState, type FormEvent, type ReactNode } from "react";
import { useAuth } from "../auth/AuthContext";
import { INSIGHTS_BUILD_ID } from "../buildId";

export function LoginPage(): ReactNode {
  const { login, loginError, clearLoginError } = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const errorId = useId();
  const passwordId = useId();
  const passwordRef = useRef<HTMLInputElement>(null);
  const inflight = useRef(false);

  async function authenticate(): Promise<void> {
    if (inflight.current) return;
    inflight.current = true;
    clearLoginError();
    setLocalError(null);
    setSubmitting(true);
    try {
      // Read live DOM value (autofill-safe). Do NOT disable the password input
      // during submit — Chrome aborts in-flight fetch when the field disables.
      const live = passwordRef.current?.value ?? "";
      const trimmed = live.trim();
      if (!trimmed) {
        setLocalError("Enter the dashboard password.");
        return;
      }
      await login(trimmed);
      if (passwordRef.current) passwordRef.current.value = "";
    } catch {
      // Error surfaced via loginError — no secrets.
    } finally {
      inflight.current = false;
      setSubmitting(false);
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    // Block native navigation / password-manager HTMLFormElement.submit races.
    event.preventDefault();
    event.stopPropagation();
    void authenticate();
  }

  const errorMessage = localError ?? loginError;

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
          Internal adoption analytics. Sign in with the shared dashboard
          password (plaintext owner password — not the Secrets Manager verifier
          JSON).
        </p>
        <form className="cs-login__form" onSubmit={onSubmit} noValidate>
          <div className="cs-field">
            <label htmlFor={passwordId}>Password</label>
            <input
              id={passwordId}
              ref={passwordRef}
              name="password"
              type="password"
              autoComplete="current-password"
              required
              aria-invalid={errorMessage ? true : undefined}
              aria-describedby={errorMessage ? errorId : undefined}
            />
          </div>
          {errorMessage ? (
            <p id={errorId} className="cs-login__error" role="alert">
              {errorMessage}
            </p>
          ) : null}
          <button type="submit" className="cs-button" disabled={submitting}>
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <p className="cs-login__build" title="Deployment identifier">
          {INSIGHTS_BUILD_ID}
        </p>
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
