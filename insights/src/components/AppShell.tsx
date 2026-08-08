import { NavLink } from "react-router-dom";
import type { ReactNode } from "react";
import { useAuth } from "../auth/AuthContext";

const NAV: ReadonlyArray<{ readonly to: string; readonly label: string; readonly end?: boolean }> = [
  { to: "/", label: "Overview", end: true },
  { to: "/adoption", label: "Adoption" },
  { to: "/assessments", label: "Assessments" },
  { to: "/technology", label: "Technology" },
  { to: "/ai", label: "AI" },
  { to: "/releases", label: "Releases" },
  { to: "/validation", label: "Validation" },
];

export function AppShell({ children }: { children: ReactNode }): ReactNode {
  const { logout } = useAuth();

  return (
    <div className="cs-app">
      <a className="cs-skip-link" href="#main">
        Skip to main content
      </a>
      <header className="cs-header" role="banner">
        <div className="cs-header__brand">
          <img
            className="cs-header__logo"
            src="/brand/codestrata-lockup-horizontal-on-light.svg"
            alt="CodeStrata"
            width={180}
            height={36}
          />
          <div className="cs-header__titles">
            <p className="cs-header__eyebrow">Internal Community Insights</p>
            <p className="cs-header__product">Community Insights</p>
          </div>
        </div>
        <div className="cs-header__actions">
          <button type="button" className="cs-button cs-button--ghost" onClick={() => void logout()}>
            Sign out
          </button>
        </div>
      </header>
      <div className="cs-layout">
        <nav className="cs-nav" aria-label="Insights sections">
          <ul>
            {NAV.map((item) => (
              <li key={item.to}>
                <NavLink to={item.to} end={item.end}>
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <main id="main" className="cs-main" tabIndex={-1}>
          {children}
        </main>
      </div>
      <footer className="cs-footer" role="contentinfo">
        <p>
          Internal adoption analytics for CodeStrata Community Edition. Not a commercial
          Platform product surface. Shared-password access. Production analytics ingestion
          is disabled. Metrics are aggregate-only.
        </p>
      </footer>
    </div>
  );
}
